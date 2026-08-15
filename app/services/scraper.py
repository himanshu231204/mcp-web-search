import logging
import re
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from app.core.config import get_config
from app.core.url_guard import UnsafeURLError, assert_url_allowed

logger = logging.getLogger(__name__)


class ScraperService:
    def __init__(self):
        self.config = get_config()
        # Redirects are followed manually so every hop can be re-validated;
        # letting httpx follow them would skip the check on the final target.
        self.client = httpx.AsyncClient(
            timeout=self.config.FETCH_TIMEOUT,
            follow_redirects=False,
            verify=False,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        )

    async def _get_validated(self, url: str) -> httpx.Response:
        """Fetch a URL, validating the original target and every redirect hop."""
        current = url

        for _ in range(self.config.MAX_REDIRECTS + 1):
            await assert_url_allowed(
                current, allow_private=self.config.ALLOW_PRIVATE_NETWORK_FETCH
            )
            response = await self.client.get(current)

            if not (response.is_redirect and response.has_redirect_location):
                response.raise_for_status()
                return response

            location = response.headers["location"]
            current = str(response.url.join(location))

        raise httpx.TooManyRedirects(
            f"Exceeded {self.config.MAX_REDIRECTS} redirects fetching {url}",
            request=httpx.Request("GET", url),
        )

    async def fetch_page(self, url: str) -> dict:
        try:
            response = await self._get_validated(url)

            soup = BeautifulSoup(response.text, "html.parser")

            title = self._extract_title(soup)
            content = self._extract_content(soup)

            if len(content) > self.config.MAX_CONTENT_LENGTH:
                content = content[: self.config.MAX_CONTENT_LENGTH] + "..."

            return {"title": title, "content": content, "url": url}
        except UnsafeURLError:
            # Policy rejection, not a fetch failure: let it reach the route
            # layer, which maps ValueError to HTTP 400 / JSON-RPC -32602.
            raise
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            return {"title": None, "content": "Request timed out", "url": url}
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            return {"title": None, "content": f"HTTP error: {str(e)}", "url": url}
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return {"title": None, "content": f"Error: {str(e)}", "url": url}

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        if soup.title:
            return soup.title.string
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return None

    def _extract_content(self, soup: BeautifulSoup) -> str:
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        return text.strip()


scraper_service = ScraperService()
