# MCP Web Search Server

A production-ready **Model Context Protocol (MCP)** server providing web search and webpage content extraction capabilities. Built with FastAPI and Server-Sent Events (SSE) for seamless OpenCode integration.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 Quick Start

### Remote Server (Recommended)

The easiest way to use the MCP Web Search Server:

```
https://mcp-web-search-nwgd.onrender.com/mcp
```

#### OpenCode Configuration

Add to your OpenCode `settings.json`:

```json
{
  "mcpServers": {
    "web-search": {
      "url": "https://mcp-web-search-nwgd.onrender.com/mcp"
    }
  }
}
```

Then verify the connection:

```bash
opencode mcp list
# Output: web-search ✓
```

---

## 🔌 Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `web_search` | Search the web using DuckDuckGo | `query` (string), `num_results` (1-20) |
| `fetch_page` | Fetch and parse webpage content | `url` (string) |

---

## 📡 API Endpoints

### MCP Endpoint (Streamable HTTP)

```
POST /mcp
Content-Type: application/json
Accept: application/json, text/event-stream
```

Primary MCP endpoint using JSON-RPC. Example initialize request:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```

Example response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-03-26",
    "capabilities": {"tools": {}},
    "serverInfo": {"name": "MCP Web Search Server", "version": "1.0.0"}
  }
}
```

### MCP SSE Compatibility Stream

```
GET /mcp
Accept: text/event-stream
```

Legacy HTTP+SSE compatibility stream. Returns:

```
event: endpoint
data: /mcp

event: message
data: {"type": "connection_ack", "message": "MCP server ready"}
```

### List Tools

```
GET /mcp/tools
```

Returns available tools with input schemas:

```json
{
  "tools": [
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
    },
    {
      "name": "fetch_page",
      "description": "Fetch webpage content",
      "input_schema": {
        "type": "object",
        "properties": {
          "url": {"type": "string", "description": "URL to fetch"}
        },
        "required": ["url"]
      }
    }
  ]
}
```

### Execute Tool (SSE)

```
POST /mcp/run
Content-Type: application/json
Accept: text/event-stream
```

Execute tools via SSE streaming:

```json
{
  "tool": "web_search",
  "input": {
    "query": "Python async programming",
    "num_results": 5
  }
}
```

**Response (SSE stream):**

```
event: start
data: {"tool": "web_search", "input": {"query": "Python async programming", "num_results": 5}}

event: data
data: {"status": "searching", "query": "Python async programming"}

event: data
data: {"status": "complete", "results": [...]}

event: end
data: {"status": "done", "tool": "web_search"}
```

### Execute Tool (MCP JSON-RPC)

Use `tools/call` via `POST /mcp`:

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "tools/call",
  "params": {
    "name": "web_search",
    "arguments": {
      "query": "AI news",
      "num_results": 3
    }
  }
}
```

### Legacy REST Endpoints

For direct HTTP calls without SSE:

```bash
# Web Search
curl -X POST https://mcp-web-search-nwgd.onrender.com/mcp/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{"query": "AI news", "num_results": 5}'

# Fetch Page
curl -X POST https://mcp-web-search-nwgd.onrender.com/mcp/tools/fetch_page \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Health Check

```
GET /
GET /health
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI App                            │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   Routes      │  │   Services   │  │    Schemas     │ │
│  │   (MCP/SSE)   │──│  (Search,    │──│   (Pydantic)   │ │
│  │               │  │   Scraper)   │  │                │ │
│  └──────────────┘  └──────────────┘  └────────────────┘ │
│         │                   │                              │
│         └───────────────────┴──────────────────────────────┤
│         ▼                                                ▼ │
│   ┌──────────────────────────────────────────────────────┐ │
│   │           Core Configuration (config.py)            │ │
│   │    Settings, Environment Variables, Defaults         │ │
│   └──────────────────────────────────────────────────────┘ │
│                                                            │
│   External Dependencies:                                   │
│   • DuckDuckGo Search API                                 │
│   • httpx (async HTTP client)                             │
│   • BeautifulSoup (HTML parsing)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Local Development

### Prerequisites

- **Python 3.11 or later**
- **pip** or your preferred package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-web-search.git
cd mcp-web-search

# Install dependencies
pip install -r requirements.txt

# (Optional) Create environment file
cp .env.example .env
```

### Running the Server

```bash
# Development (with auto-reload)
python -m app.main

# Production
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

The server will start on `http://localhost:10000`

### Testing SSE Endpoints

```bash
# Test MCP root SSE
curl -N http://localhost:10000/mcp

# Test tool list
curl http://localhost:10000/mcp/tools | jq
```

---

## ⚙️ Configuration

Environment variables (`.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | MCP Web Search Server | Application name |
| `VERSION` | 1.0.0 | Application version |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 10000 | Server port |
| `DEFAULT_NUM_RESULTS` | 5 | Default search results |
| `MAX_NUM_RESULTS` | 20 | Maximum results per request |
| `SEARCH_TIMEOUT` | 10 | Search timeout (seconds) |
| `FETCH_TIMEOUT` | 10 | Page fetch timeout (seconds) |
| `MCP_REQUEST_TIMEOUT` | 25 | Max timeout for one MCP tool call (seconds) |
| `SSE_HEARTBEAT_INTERVAL` | 5 | Heartbeat interval for SSE stream (seconds) |
| `MAX_CONTENT_LENGTH` | 5000 | Max content characters |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| [FastAPI](https://fastapi.tiangolo.com/) | Web framework |
| [httpx](https://www.python-httpx.org/) | Async HTTP client |
| [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing |
| [duckduckgo-search](https://github.com/deedy5/duckduckgo_search) | DuckDuckGo API |
| [uvicorn](https://www.uvicorn.org/) | ASGI server |
| [pydantic](https://docs.pydantic.dev/) | Data validation |

---

## 🔧 Code Quality

```bash
# Linting
ruff check app/

# Auto-fix
ruff check --fix app/

# Formatting
black app/

# Type checking
mypy app/
```

---

## 🐳 Docker Deployment

```bash
# Build
docker build -t mcp-web-search .

# Run
docker run -p 10000:10000 mcp-web-search
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [DuckDuckGo](https://duckduckgo.com/) - Search API
- [Model Context Protocol](https://modelcontextprotocol.io/) - AI tool integration standard

---

**Last Updated**: 2026-04-04  
**Status**: Production Ready ✅
