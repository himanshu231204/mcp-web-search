import logging
import json
import asyncio
from typing import Any, AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.models import (
    WebSearchRequest,
    WebSearchResponse,
    FetchPageRequest,
    FetchPageResponse,
    MCPToolsResponse,
    MCPTool,
    SearchResult,
    MCPToolExecutionRequest,
)
from app.services.search import search_service
from app.services.scraper import scraper_service

logger = logging.getLogger(__name__)

mcp_router = APIRouter(tags=["MCP Root"])
router = APIRouter(prefix="/tools", tags=["MCP Tools"])
exec_router = APIRouter(prefix="/run", tags=["MCP Execute"])


def format_sse(event: str, data: Any) -> str:
    """Format data as SSE message."""
    json_data = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {json_data}\n\n"


async def sse_generator():
    """Generate SSE stream for MCP root connection - long-lived for OpenCode."""
    # Initial handshake
    yield format_sse(
        "ready", {"status": "ok", "message": "MCP Web Search Server ready"}
    )

    # Keep connection alive with periodic ping events
    try:
        while True:
            await asyncio.sleep(10)
            yield format_sse("ping", {"status": "alive"})
    except asyncio.CancelledError:
        yield format_sse("close", {"status": "disconnected"})


@mcp_router.get("")
async def mcp_root():
    """MCP root endpoint - SSE stream for OpenCode compatibility."""
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@mcp_router.get("/")
async def mcp_root_slash():
    """MCP root endpoint with trailing slash - SSE stream."""
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def execute_tool_stream(
    tool_name: str, tool_input: dict
) -> AsyncGenerator[str, None]:
    """Execute a tool and yield SSE events."""
    # Start event
    yield format_sse("start", {"tool": tool_name, "input": tool_input})

    try:
        if tool_name == "web_search":
            query = tool_input.get("query", "")
            num_results = tool_input.get("num_results", 5)

            yield format_sse("data", {"status": "searching", "query": query})

            results = await search_service.search(query=query, num_results=num_results)

            yield format_sse("data", {"status": "complete", "results": results})

        elif tool_name == "fetch_page":
            url = tool_input.get("url", "")

            yield format_sse("data", {"status": "fetching", "url": url})

            result = await scraper_service.fetch_page(url=url)

            yield format_sse("data", {"status": "complete", "result": result})

        else:
            yield format_sse("error", {"message": f"Unknown tool: {tool_name}"})
            return

    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        yield format_sse("error", {"message": str(e)})
        return

    # End event
    yield format_sse("end", {"status": "done", "tool": tool_name})


@exec_router.post("")
async def run_tool(request: MCPToolExecutionRequest):
    """Execute a tool via SSE stream."""
    return StreamingResponse(
        execute_tool_stream(request.tool, request.input), media_type="text/event-stream"
    )


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
