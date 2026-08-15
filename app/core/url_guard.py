"""URL safety checks for outbound fetches (SSRF protection)."""

import asyncio
import ipaddress
import logging
import socket
from typing import List, Union
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = frozenset({"http", "https"})

IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]

# Ranges the stdlib does not flag via is_private but that should never be
# reachable from a public-facing fetcher.
EXTRA_BLOCKED_NETWORKS = (
    ipaddress.ip_network("100.64.0.0/10"),  # RFC 6598 shared address space (CGNAT)
    ipaddress.ip_network("192.0.0.0/24"),  # RFC 6890 IETF protocol assignments
)


class UnsafeURLError(ValueError):
    """Raised when a URL is rejected by policy before any request is made.

    Subclasses ValueError so the existing route handlers map it to HTTP 400
    and JSON-RPC -32602 without further plumbing.
    """


class URLResolutionError(RuntimeError):
    """Raised when a hostname cannot be resolved.

    This is an upstream failure rather than a policy rejection, so callers
    should surface it the same way as any other fetch error.
    """


def _is_blocked_ip(ip: IPAddress) -> bool:
    """Return True if the address is not a routable public destination."""
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        return _is_blocked_ip(mapped)

    sixtofour = getattr(ip, "sixtofour", None)
    if sixtofour is not None:
        return _is_blocked_ip(sixtofour)

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    ):
        return True

    return any(ip in network for network in EXTRA_BLOCKED_NETWORKS)


def _resolve_host(host: str) -> List[IPAddress]:
    """Resolve a hostname to every address it maps to.

    A literal IP is returned as-is. Every address is checked, so a hostname
    with both a public A record and a private AAAA record is still rejected.
    """
    try:
        return [ipaddress.ip_address(host)]
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise URLResolutionError(f"Could not resolve host: {host}") from exc

    addresses = []
    for info in infos:
        sockaddr = info[4]
        try:
            addresses.append(ipaddress.ip_address(sockaddr[0]))
        except ValueError:
            continue

    if not addresses:
        raise URLResolutionError(f"Could not resolve host: {host}")

    return addresses


async def assert_url_allowed(url: str, allow_private: bool = False) -> None:
    """Validate a URL before it is fetched.

    Raises:
        UnsafeURLError: the scheme is not http/https, the URL has no host, or
            the host resolves to a non-public address.
        URLResolutionError: the hostname could not be resolved.
    """
    try:
        parts = urlsplit(url)
    except ValueError as exc:
        raise UnsafeURLError(f"Malformed URL: {url}") from exc

    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeURLError(
            f"Unsupported URL scheme '{parts.scheme}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_SCHEMES))}"
        )

    try:
        host = parts.hostname
    except ValueError as exc:
        raise UnsafeURLError(f"Malformed URL host: {url}") from exc

    if not host:
        raise UnsafeURLError(f"URL is missing a host: {url}")

    if allow_private:
        return

    # getaddrinfo blocks, so keep it off the event loop.
    addresses = await asyncio.to_thread(_resolve_host, host)

    for address in addresses:
        if _is_blocked_ip(address):
            logger.warning("Blocked fetch of non-public address %s (%s)", host, address)
            raise UnsafeURLError(
                f"Refusing to fetch '{host}': resolves to non-public address {address}"
            )
