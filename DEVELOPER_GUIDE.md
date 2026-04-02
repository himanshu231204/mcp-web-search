# Developer Guide

This guide covers the internal architecture, development setup, and extension patterns for the MCP Web Search Server.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI App                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Routes    │  │  Services   │  │   Schemas   │     │
│  │  (mcp.py)   │──│ (search,    │──│  (models)   │     │
│  │             │  │  scraper)   │  │             │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│         │                  │                              │
│         ▼                  ▼                              │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Core (config.py)                    │    │
│  │         Settings & Environment Vars             │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Folder Structure

```
mcp-web-search/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Configuration & settings
│   ├── routes/
│   │   ├── __init__.py
│   │   └── mcp.py          # MCP endpoint handlers
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── models.py       # Pydantic request/response models
│   └── services/
│       ├── __init__.py
│       ├── search.py       # DuckDuckGo search logic
│       └── scraper.py      # Webpage fetching logic
├── requirements.txt
├── Dockerfile
├── render.yaml
├── .env.example
├── README.md
└── DEVELOPER_GUIDE.md
```

## How Each Module Works

### Core (config.py)

The `Config` class centralizes all application settings using Pydantic and environment variables via `python-dotenv`.

- Loads settings from `.env` file (if present)
- Provides sensible defaults
- Uses `lru_cache` for singleton access

Key settings:
- `DEFAULT_NUM_RESULTS`: Default search results (default: 5)
- `MAX_NUM_RESULTS`: Maximum allowed results (default: 20)
- `FETCH_TIMEOUT`: HTTP timeout for page fetching (default: 10s)
- `SEARCH_TIMEOUT`: Timeout for search requests (default: 10s)
- `MAX_CONTENT_LENGTH`: Max characters in fetched content (default: 5000)
- `RATE_LIMIT_PER_MINUTE`: Rate limit per IP (default: 20)

### Schemas (models.py)

Defines Pydantic models for request/response validation:

- `WebSearchRequest`: query (required), num_results (optional, 1-20)
- `WebSearchResponse`: list of SearchResult objects
- `FetchPageRequest`: url (required)
- `FetchPageResponse`: title, content, url
- `MCPToolsResponse`: list of MCPTool definitions

### Services

#### search.py

Uses `duckduckgo_search` (DDGS) to perform web searches:

- Wraps sync DDGS with `asyncio.to_thread()` for async compatibility
- Returns list of dicts with title, url, snippet
- Handles errors gracefully, returns empty list on failure

#### scraper.py

Uses `httpx` (async HTTP client) and `BeautifulSoup` (HTML parsing):

- Configured with timeout and redirect following
- Extracts title from `<title>` tag or first `<h1>`
- Removes `<script>` and `<style>` tags before extracting text
- Truncates content to `MAX_CONTENT_LENGTH`
- Handles timeouts, HTTP errors, and generic exceptions

### Routes (mcp.py)

FastAPI router providing MCP-compatible endpoints:

- `GET /mcp/tools` - Returns tool definitions with JSON Schema input schemas
- `POST /mcp/tools/web_search` - Delegates to search service
- `POST /mcp/tools/fetch_page` - Delegates to scraper service

### Main (main.py)

Creates FastAPI application with:

- CORS middleware (allows all origins)
- Routes included
- Root and health check endpoints

## MCP Integration

The server implements the MCP protocol for tool discovery:

1. **Tool Listing** (`GET /mcp/tools`): Returns JSON Schema definitions for each tool
2. **Tool Execution**: POST to specific tool endpoints with JSON body

The tool definitions use JSON Schema format compatible with MCP clients:

```json
{
  "name": "web_search",
  "description": "Search the web using DuckDuckGo",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Search query"},
      "num_results": {"type": "integer", "description": "Number of results (1-20)", "default": 5}
    },
    "required": ["query"]
  }
}
```

## Extending with New Tools

To add a new MCP tool:

1. **Add request/response schemas** in `schemas/models.py`
2. **Create service** in `services/` (or extend existing)
3. **Add route** in `routes/mcp.py`
4. **Update tool list** in `GET /mcp/tools`

Example: Adding an "image_search" tool:

```python
# schemas/models.py
class ImageSearchRequest(BaseModel):
    query: str
    num_results: int = Field(default=5, ge=1, le=20)

class ImageSearchResponse(BaseModel):
    results: List[ImageResult]

# services/image_search.py
class ImageSearchService:
    async def search(self, query: str, num_results: int) -> List[dict]:
        # Implementation
        pass

# routes/mcp.py
@router.post("/image_search", response_model=ImageSearchResponse)
async def image_search(request: ImageSearchRequest):
    result = await image_service.search(...)
    return ImageSearchResponse(results=result)
```

## Environment Variables

Create a `.env` file based on `.env.example`:

| Variable | Description | Default |
|----------|-------------|---------|
| APP_NAME | Application name | MCP Web Search Server |
| VERSION | Version string | 1.0.0 |
| HOST | Server host | 0.0.0.0 |
| PORT | Server port | 10000 |
| DEFAULT_NUM_RESULTS | Default search count | 5 |
| MAX_NUM_RESULTS | Max search count | 20 |
| SEARCH_TIMEOUT | Search timeout (seconds) | 10 |
| FETCH_TIMEOUT | Fetch timeout (seconds) | 10 |
| MAX_CONTENT_LENGTH | Max content chars | 5000 |
| RATE_LIMIT_PER_MINUTE | Rate limit | 20 |

## Local Development Setup

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate   # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run development server**:
   ```bash
   python -m app.main
   # or
   uvicorn app.main:app --reload
   ```

4. **Test endpoints**:
   ```bash
   curl http://localhost:10000/mcp/tools
   curl -X POST http://localhost:10000/mcp/tools/web_search \
     -H "Content-Type: application/json" \
     -d '{"query": "test"}'
   ```

## Debugging Tips

1. **Enable debug logging**: Modify `logging.basicConfig` in `main.py` to set `level=logging.DEBUG`

2. **Test services directly**:
   ```python
   from app.services.search import search_service
   
   results = await search_service.search("python", 5)
   print(results)
   ```

3. **Check HTTP errors**: The scraper logs all HTTP errors with the URL

4. **Validate requests**: Use Pydantic validation errors which return clear messages

5. **Render deployment logs**: Check Render dashboard for runtime errors

## Rate Limiting

Currently implemented as configuration only. For production rate limiting, consider:

- FastAPI middleware with `slowapi`
- Redis-based distributed rate limiting
- API Gateway-level rate limiting

## Caching

Simple in-memory LRU caching can be added using `functools.lru_cache` or `cachetools`:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str, num_results: int):
    # Implementation
    pass
```

For production, consider Redis caching for distributed deployments.

## Error Handling

All endpoints:
- Catch and log exceptions
- Return 500 with error detail on failure
- Use HTTPException for client errors

Service layer:
- Returns empty results on search failure
- Returns error message in response on fetch failure
- Never raises unhandled exceptions

## Production Considerations

1. **HTTPS**: Render provides automatic HTTPS
2. **CORS**: Currently allows all origins - restrict in production
3. **Monitoring**: Add logging/observability (Sentry, DataDog)
4. **Security**: Validate URLs in fetch_page to prevent SSRF
5. **Rate limiting**: Implement actual rate limiting middleware