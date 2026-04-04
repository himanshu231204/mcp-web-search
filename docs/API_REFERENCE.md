# API Reference

This document defines the public API behavior for the MCP Web Search Server.

## Base URL

- Local: http://localhost:10000
- Render: https://mcp-web-search-nwgd.onrender.com

## Transport Modes

1. Primary MCP transport: JSON-RPC over Streamable HTTP at POST /mcp
2. Compatibility stream: GET /mcp (SSE)
3. Legacy REST routes: /mcp/tools/* and /mcp/run

## Health Endpoints

### GET /

Purpose:
- Basic service metadata and running status.

Response (200):
```json
{
  "name": "MCP Web Search Server",
  "version": "1.0.0",
  "status": "running"
}
```

### GET /health

Purpose:
- Liveness check for deployment and uptime monitoring.

Response (200):
```json
{
  "status": "healthy"
}
```

## MCP Endpoint (Primary)

### POST /mcp

Headers:
- Content-Type: application/json
- Accept: application/json, text/event-stream

Body:
- JSON-RPC request object.

### Supported Methods

1. initialize
2. notifications/initialized
3. tools/list
4. tools/call

### Method: initialize

Request:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-03-26",
    "capabilities": {"tools": {}},
    "serverInfo": {
      "name": "MCP Web Search Server",
      "version": "1.0.0"
    }
  }
}
```

### Method: notifications/initialized

Request:
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized",
  "params": {}
}
```

Response:
- HTTP 202 Accepted

### Method: tools/list

Request:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "web_search",
        "description": "Search the web using DuckDuckGo",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {"type": "string", "description": "Search query"},
            "num_results": {
              "type": "integer",
              "description": "Number of results (1-20)",
              "default": 5
            }
          },
          "required": ["query"]
        }
      },
      {
        "name": "fetch_page",
        "description": "Fetch webpage content",
        "inputSchema": {
          "type": "object",
          "properties": {
            "url": {"type": "string", "description": "URL to fetch"}
          },
          "required": ["url"]
        }
      }
    ]
  }
}
```

### Method: tools/call

Request (web_search):
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "web_search",
    "arguments": {
      "query": "python async",
      "num_results": 3
    }
  }
}
```

Request (fetch_page):
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "fetch_page",
    "arguments": {
      "url": "https://example.com"
    }
  }
}
```

Success response:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"results\":[...]}"
      }
    ],
    "isError": false
  }
}
```

## JSON-RPC Error Behavior

Method not found:
```json
{
  "jsonrpc": "2.0",
  "id": 77,
  "error": {
    "code": -32601,
    "message": "Method not found: unknown/method"
  }
}
```

Invalid request:
- code: -32600

Invalid tool call arguments or unknown tool:
- code: -32602

Timeout during tool execution:
- code: -32000

## Compatibility Endpoints

### GET /mcp

SSE compatibility stream.

First event:
```text
event: endpoint
data: /mcp
```

Then periodic message heartbeat events.

### POST /mcp/run

SSE streaming tool execution endpoint.

Input:
```json
{
  "tool": "web_search",
  "input": {
    "query": "AI news",
    "num_results": 5
  }
}
```

Events:
- start
- data (searching/fetching)
- data (complete)
- end

## Legacy REST Endpoints

### GET /mcp/tools

Returns compatibility tool definitions with input_schema (snake_case).

### POST /mcp/tools/web_search

Request:
```json
{
  "query": "python programming",
  "num_results": 5
}
```

Response:
```json
{
  "results": [
    {
      "title": "...",
      "url": "...",
      "snippet": "..."
    }
  ]
}
```

### POST /mcp/tools/fetch_page

Request:
```json
{
  "url": "https://example.com"
}
```

Response:
```json
{
  "title": "Example Domain",
  "content": "...",
  "url": "https://example.com"
}
```

## Timeouts and Limits

Config-driven defaults:

1. SEARCH_TIMEOUT: 10s
2. FETCH_TIMEOUT: 10s
3. MCP_REQUEST_TIMEOUT: 25s
4. MAX_NUM_RESULTS: 20
5. MAX_CONTENT_LENGTH: 5000 chars

## Backward Compatibility Notes

1. MCP clients should use POST /mcp.
2. Legacy routes are retained for compatibility and debugging.
3. tools/list over MCP returns inputSchema (camelCase).
4. GET /mcp/tools returns input_schema (snake_case).
