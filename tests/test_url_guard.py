"""Tests for SSRF protection on outbound fetches."""

import ipaddress

import httpx
import pytest

from app.core import url_guard
from app.core.url_guard import UnsafeURLError, URLResolutionError, assert_url_allowed
from app.services.scraper import scraper_service


@pytest.fixture
def fake_dns(monkeypatch: pytest.MonkeyPatch):
    """Map hostnames to fixed addresses so tests never touch real DNS."""
    table: dict[str, list[str]] = {}

    def _resolve(host: str):
        try:
            return [ipaddress.ip_address(host)]
        except ValueError:
            pass
        if host not in table:
            raise URLResolutionError(f"Could not resolve host: {host}")
        return [ipaddress.ip_address(a) for a in table[host]]

    monkeypatch.setattr(url_guard, "_resolve_host", _resolve)
    return table


BLOCKED_URLS = [
    "http://127.0.0.1:8931/internal",
    "http://localhost/admin",
    "http://169.254.169.254/latest/meta-data/",  # cloud metadata
    "http://10.0.0.5/",
    "http://192.168.1.1/",
    "http://172.16.0.1/",
    "http://[::1]/",
    "http://[::ffff:127.0.0.1]/",  # IPv4-mapped loopback
    "http://0.0.0.0/",
    "http://100.64.0.1/",  # CGNAT shared address space
]


@pytest.mark.asyncio
@pytest.mark.parametrize("url", BLOCKED_URLS)
async def test_private_addresses_are_rejected(url: str, fake_dns):
    fake_dns["localhost"] = ["127.0.0.1"]
    with pytest.raises(UnsafeURLError):
        await assert_url_allowed(url)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/x",
        "gopher://example.com/",
        "data:text/html,hello",
        "not-a-url",
    ],
)
async def test_non_http_schemes_are_rejected(url: str, fake_dns):
    with pytest.raises(UnsafeURLError):
        await assert_url_allowed(url)


@pytest.mark.asyncio
async def test_url_without_host_is_rejected(fake_dns):
    with pytest.raises(UnsafeURLError):
        await assert_url_allowed("http:///nohost")


@pytest.mark.asyncio
async def test_public_address_is_allowed(fake_dns):
    fake_dns["example.com"] = ["93.184.216.34"]
    await assert_url_allowed("https://example.com/page")


@pytest.mark.asyncio
async def test_host_with_one_private_record_is_rejected(fake_dns):
    """A hostname is only safe if *every* address it resolves to is public."""
    fake_dns["split.example"] = ["93.184.216.34", "127.0.0.1"]
    with pytest.raises(UnsafeURLError):
        await assert_url_allowed("https://split.example/")


@pytest.mark.asyncio
async def test_unresolvable_host_is_not_a_policy_error(fake_dns):
    """DNS failure is an upstream error, not an SSRF rejection."""
    with pytest.raises(URLResolutionError):
        await assert_url_allowed("https://nonexistent.invalid/")


@pytest.mark.asyncio
async def test_allow_private_escape_hatch_skips_checks(fake_dns):
    await assert_url_allowed("http://127.0.0.1/", allow_private=True)


@pytest.mark.asyncio
async def test_fetch_page_rejects_private_url(fake_dns):
    with pytest.raises(UnsafeURLError):
        await scraper_service.fetch_page("http://169.254.169.254/latest/meta-data/")


@pytest.mark.asyncio
async def test_fetch_page_rejects_redirect_to_private_address(
    fake_dns, monkeypatch: pytest.MonkeyPatch
):
    """The guard must re-run on each hop, not just the submitted URL."""
    fake_dns["public.example"] = ["93.184.216.34"]

    async def fake_get(url, *args, **kwargs):
        request = httpx.Request("GET", url)
        if "public.example" in str(url):
            return httpx.Response(
                302,
                headers={"location": "http://169.254.169.254/latest/meta-data/"},
                request=request,
            )
        return httpx.Response(
            200, text="<html><title>leaked</title></html>", request=request
        )

    monkeypatch.setattr(scraper_service.client, "get", fake_get)

    with pytest.raises(UnsafeURLError):
        await scraper_service.fetch_page("http://public.example/redirect")


@pytest.mark.asyncio
async def test_fetch_page_follows_public_redirect(
    fake_dns, monkeypatch: pytest.MonkeyPatch
):
    fake_dns["a.example"] = ["93.184.216.34"]
    fake_dns["b.example"] = ["93.184.216.35"]

    async def fake_get(url, *args, **kwargs):
        request = httpx.Request("GET", url)
        if "a.example" in str(url):
            return httpx.Response(
                302, headers={"location": "http://b.example/final"}, request=request
            )
        return httpx.Response(
            200,
            text="<html><title>Final</title><body>ok</body></html>",
            request=request,
        )

    monkeypatch.setattr(scraper_service.client, "get", fake_get)

    result = await scraper_service.fetch_page("http://a.example/start")
    assert result["title"] == "Final"
    assert "ok" in result["content"]


@pytest.mark.asyncio
async def test_fetch_page_stops_after_max_redirects(
    fake_dns, monkeypatch: pytest.MonkeyPatch
):
    fake_dns["loop.example"] = ["93.184.216.34"]

    async def fake_get(url, *args, **kwargs):
        return httpx.Response(
            302,
            headers={"location": "http://loop.example/next"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(scraper_service.client, "get", fake_get)

    result = await scraper_service.fetch_page("http://loop.example/start")
    # Redirect loops stay a fetch error, not a policy rejection.
    assert "HTTP error" in result["content"]
