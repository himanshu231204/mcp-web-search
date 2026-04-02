import logging
from fastapi import APIRouter, HTTPException
from app.schemas.models import (
    WebSearchRequest,
    WebSearchResponse,
    FetchPageRequest,
    FetchPageResponse,
    MCPToolsResponse,
    MCPTool,
    SearchResult,
)
from app.services.search import search_service
from app.services.scraper import scraper_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp/tools", tags=["MCP Tools"])


@router.get("", response_model=MCPToolsResponse)
async def list_tools():
    return MCPToolsResponse(
        tools=[
            MCPTool(
                name="web_search",
                description="Search the web using DuckDuckGo",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results (1-20)",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            ),
            MCPTool(
                name="fetch_page",
                description="Fetch webpage content",
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to fetch"}
                    },
                    "required": ["url"],
                },
            ),
        ]
    )


@router.post("/web_search", response_model=WebSearchResponse)
async def web_search(request: WebSearchRequest):
    try:
        results = await search_service.search(
            query=request.query, num_results=request.num_results
        )
        return WebSearchResponse(results=[SearchResult(**r) for r in results])
    except Exception as e:
        logger.error(f"Web search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch_page", response_model=FetchPageResponse)
async def fetch_page(request: FetchPageRequest):
    try:
        result = await scraper_service.fetch_page(url=request.url)
        return FetchPageResponse(**result)
    except Exception as e:
        logger.error(f"Fetch page error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
