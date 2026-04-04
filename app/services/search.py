import logging
from typing import List
import asyncio
from duckduckgo_search import DDGS
from app.core.config import get_config

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self):
        self.ddgs = DDGS()
        self.config = get_config()

    async def search(self, query: str, num_results: int = 5) -> List[dict]:
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(
                    self.ddgs.text, keywords=query, max_results=num_results
                ),
                timeout=self.config.SEARCH_TIMEOUT,
            )

            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                }
                for r in results
            ]
        except asyncio.TimeoutError:
            logger.warning("Search timeout for query: %s", query)
            return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []


search_service = SearchService()
