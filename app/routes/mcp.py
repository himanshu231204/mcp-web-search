import logging
import json
import asyncio
from typing import Any, AsyncGenerator
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse
from app.core.config import get_config
from app.schemas.models import (
    WebSearchRequest,
    WebSearchResponse,
    FetchPageRequest,
    FetchPageResponse,
    MCPToolsResponse,
    MCPTool,
    SearchResult,
    MCPToolExecutionRequest,
    JSONRPCRequest,
)
from app.services.search import search_service
from app.services.scraper import scraper_service

logger = logging.getLogger(__name__)
config = get_config()

mcp_router = APIRouter(tags=["MCP Root"])
router = APIRouter(prefix="/tools", tags=["MCP Tools"])
exec_router = APIRouter(prefix="/run", tags=["MCP Execute"])


def format_sse(event: str, data: Any) -> str:
    """Format data as SSE message."""
    json_data = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {json_data}\n\n"


def _tool_definitions() -> list[MCPTool]:
    return [
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


def _mcp_tool_definitions() -> list[dict[str, Any]]:
    """Return MCP-compliant tool definitions for JSON-RPC tools/list."""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.input_schema,
        }
        for tool in _tool_definitions()
    ]


async def _execute_tool(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "web_search":
        results = await asyncio.wait_for(
            search_service.search(
                query=tool_input.get("query", ""),
                num_results=tool_input.get("num_results", config.DEFAULT_NUM_RESULTS),
            ),
            timeout=config.MCP_REQUEST_TIMEOUT,
        )
        return {"results": results}

    if tool_name == "fetch_page":
        result = await asyncio.wait_for(
            scraper_service.fetch_page(url=tool_input.get("url", "")),
            timeout=config.MCP_REQUEST_TIMEOUT,
        )
        return result

    raise ValueError(f"Unknown tool: {tool_name}")


def _jsonrpc_result(request_id: Any, result: dict[str, Any]) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": result})


def _jsonrpc_error(request_id: Any, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        }
    )


async def sse_generator():
    """Generate SSE stream for MCP root connection."""
    # Legacy HTTP+SSE compatibility: endpoint must be first event.
    yield format_sse("endpoint", "/mcp")
    yield format_sse("message", {"type": "connection_ack", "message": "MCP server ready"})

    try:
        while True:
            await asyncio.sleep(config.SSE_HEARTBEAT_INTERVAL)
            yield format_sse("message", {"type": "heartbeat", "status": "alive"})
    except asyncio.CancelledError:
        logger.info("MCP SSE connection closed")


@mcp_router.post("")
async def mcp_post(request: JSONRPCRequest):
    """MCP endpoint using Streamable HTTP + JSON-RPC."""
    if request.jsonrpc != "2.0":
        return _jsonrpc_error(request.id, -32600, "Invalid Request")

    method = request.method

    if method == "initialize":
        return _jsonrpc_result(
            request.id,
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": config.APP_NAME, "version": config.VERSION},
            },
        )

    if method == "notifications/initialized":
        return Response(status_code=202)

    if method == "tools/list":
        return _jsonrpc_result(
            request.id,
            {"tools": _mcp_tool_definitions()},
        )

    if method == "tools/call":
        tool_name = request.params.get("name")
        tool_input = request.params.get("arguments", {})

        if not tool_name:
            return _jsonrpc_error(request.id, -32602, "Missing required parameter: name")

        try:
            tool_result = await _execute_tool(str(tool_name), dict(tool_input))
            return _jsonrpc_result(
                request.id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(tool_result),
                        }
                    ],
                    "isError": False,
                },
            )
        except asyncio.TimeoutError:
            return _jsonrpc_error(request.id, -32000, "Tool call timed out")
        except ValueError as exc:
            return _jsonrpc_error(request.id, -32602, str(exc))

    return _jsonrpc_error(request.id, -32601, f"Method not found: {method}")


@mcp_router.post("/")
async def mcp_post_slash(request: JSONRPCRequest):
    """MCP endpoint with trailing slash for compatibility."""
    return await mcp_post(request)


@mcp_router.get("")
async def mcp_root():
    """MCP root endpoint - SSE stream compatibility endpoint."""
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
            yield format_sse("data", {"status": "searching", "query": tool_input.get("query", "")})
        elif tool_name == "fetch_page":
            yield format_sse("data", {"status": "fetching", "url": tool_input.get("url", "")})

        result = await _execute_tool(tool_name=tool_name, tool_input=tool_input)

        if tool_name == "web_search":
            yield format_sse("data", {"status": "complete", "results": result["results"]})
        else:
            yield format_sse("data", {"status": "complete", "result": result})

    except asyncio.TimeoutError:
        yield format_sse("error", {"message": "Tool execution timed out"})
        return
    except ValueError as e:
        yield format_sse("error", {"message": str(e)})
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
    return MCPToolsResponse(tools=_tool_definitions())


@router.post("/web_search", response_model=WebSearchResponse)
async def web_search(request: WebSearchRequest):
    try:
        result = await _execute_tool(
            "web_search", {"query": request.query, "num_results": request.num_results}
        )
        return WebSearchResponse(results=[SearchResult(**r) for r in result["results"]])
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Search request timed out")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Web search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch_page", response_model=FetchPageResponse)
async def fetch_page(request: FetchPageRequest):
    try:
        result = await _execute_tool("fetch_page", {"url": request.url})
        return FetchPageResponse(**result)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Fetch request timed out")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Fetch page error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
