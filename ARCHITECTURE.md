# MCP Web Search Server Architecture

## 1. Purpose

This document describes the architecture of the MCP Web Search Server in this repository. It explains the runtime structure, request flows, reliability patterns, and extension points so contributors can modify the system safely.

## 2. System Overview

The service is a FastAPI application that exposes:

1. Primary MCP endpoint via JSON-RPC (`POST /mcp`)
2. Compatibility stream endpoint (`GET /mcp`)
3. Legacy REST tool endpoints (`/mcp/tools/*`)
4. SSE execution endpoint (`POST /mcp/run`)

Core capabilities:

1. `web_search`: searches the web using DuckDuckGo
2. `fetch_page`: fetches and parses webpage content

## 3. Architectural Style

The system follows a layered modular backend pattern:

1. Transport/Route layer: HTTP routes, JSON-RPC method routing, SSE formatting
2. Schema layer: Pydantic models for validation and response contracts
3. Service layer: business logic for search and scraping
4. Configuration layer: environment-driven runtime settings

This separation keeps protocol logic independent from tool implementation details.

## 4. High-Level Component Diagram

```text
+-------------------------- Clients --------------------------+
|  OpenCode / MCP clients / curl / REST callers              |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
| FastAPI App (app/main.py)                                  |
|  - CORS middleware                                          |
|  - Router mounting under /mcp                              |
+------------------------------+------------------------------+
                               |
                               v
+------------------------ Route Layer ------------------------+
| app/routes/mcp.py                                            |
|  - POST /mcp (JSON-RPC MCP)                                 |
|  - GET /mcp (SSE compatibility)                             |
|  - GET /mcp/tools                                            |
|  - POST /mcp/tools/web_search                               |
|  - POST /mcp/tools/fetch_page                               |
|  - POST /mcp/run (SSE tool execution)                       |
+------------------------------+------------------------------+
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
+------------------------------+   +--------------------------+
| Search Service               |   | Scraper Service          |
| app/services/search.py       |   | app/services/scraper.py  |
| - DuckDuckGo search          |   | - HTTP fetch via httpx   |
| - Result normalization       |   | - HTML parse via BS4     |
+------------------------------+   +--------------------------+
                 |                           |
                 +-------------+-------------+
                               v
+-------------------------------------------------------------+
| External Dependencies                                       |
|  - DuckDuckGo Search                                        |
|  - Public websites                                          |
+-------------------------------------------------------------+
```

## 5. Repository Component Map

1. `app/main.py`
: FastAPI bootstrap, middleware setup, route inclusion.

2. `app/core/config.py`
: Typed configuration loaded from environment defaults.

3. `app/routes/mcp.py`
: MCP transport handlers, method dispatch, SSE compatibility, legacy endpoints.

4. `app/schemas/models.py`
: Request/response contracts and JSON-RPC model definitions.

5. `app/services/search.py`
: DuckDuckGo integration with timeout-protected execution.

6. `app/services/scraper.py`
: HTTP fetch, HTML extraction, content normalization/truncation.

7. `tests/test_routes.py`
: Route behavior and protocol contract tests.

8. `tests/test_services.py`
: Service behavior tests and resilience checks.

## 6. Request Flow: MCP JSON-RPC

### 6.1 Initialize

1. Client sends `POST /mcp` with method `initialize`
2. Route validates JSON-RPC envelope
3. Server returns protocol version, capabilities, and server info

### 6.2 Tool Discovery

1. Client sends `POST /mcp` with method `tools/list`
2. Route returns MCP-compliant tool definitions
3. Response uses `inputSchema` (camelCase) for MCP compatibility

### 6.3 Tool Execution (`tools/call`)

1. Client sends `POST /mcp` method `tools/call`
2. Route extracts `name` + `arguments`
3. `_execute_tool` dispatches to corresponding service
4. Service returns normalized result
5. Route wraps result in MCP content envelope

## 7. Request Flow: Legacy and Compatibility Endpoints

### 7.1 SSE compatibility (`GET /mcp`)

1. Opens text/event-stream response
2. Sends initial `endpoint` event
3. Sends connection ack
4. Sends periodic heartbeat messages

### 7.2 Legacy REST tools

1. `POST /mcp/tools/web_search`
2. `POST /mcp/tools/fetch_page`

These are compatibility routes for direct HTTP callers and debugging.

## 8. Data Contracts

The schema layer enforces:

1. Search input bounds (`query`, `num_results`)
2. Fetch input shape (`url`)
3. JSON-RPC envelope structure
4. Tool list and tool execution response models

Contract stability is critical for MCP client compatibility.

## 9. Reliability Design

Reliability controls include:

1. Search timeout (`SEARCH_TIMEOUT`) in search service
2. Fetch timeout (`FETCH_TIMEOUT`) in scraper client
3. Route-level tool timeout (`MCP_REQUEST_TIMEOUT`)
4. Fallback responses for upstream failures
5. Health endpoint for deployment checks

These controls prevent unbounded waits and improve behavior under upstream instability.

## 10. Error Handling Strategy

1. Validation errors handled by Pydantic/FastAPI
2. Unknown JSON-RPC methods return method-not-found errors
3. Unknown tools return argument/error responses
4. Timeouts return deterministic timeout errors
5. Service exceptions are logged and mapped to safe outputs

## 11. Security Considerations

Current baseline:

1. Input validation via schemas
2. Bounded timeouts
3. Max content length enforcement

Recommended future hardening:

1. URL allow/deny policy for fetch tool
2. SSRF protections for private/internal addresses
3. Rate limiting for public deployments
4. Structured log redaction policy

## 12. Performance Considerations

Main latency contributors:

1. Upstream DuckDuckGo response times
2. Remote webpage response times
3. HTML parsing cost

Performance controls:

1. Timeout bounds
2. Content truncation
3. Async execution model

Potential future optimizations:

1. Result caching for repeated search queries
2. Connection pool tuning
3. Tool-specific latency metrics

## 13. Deployment View

Platform target in this repository is Render.

Startup path:

1. Install dependencies from `requirements.txt`
2. Start app with `uvicorn app.main:app --host 0.0.0.0 --port 10000`

Runtime validation checks:

1. `GET /health`
2. `POST /mcp` initialize
3. `POST /mcp` tools/list
4. `POST /mcp` tools/call

## 14. Test Architecture

Tests are structured by concern:

1. Route tests: protocol and endpoint behavior
2. Service tests: integration and resilience behavior

Critical regression tests should always include:

1. MCP initialize response shape
2. MCP tools/list key naming (`inputSchema`)
3. Tool execution envelope and error handling

## 15. Extension Guidelines

When adding a new MCP tool:

1. Add schemas in `app/schemas/models.py`
2. Add implementation in `app/services/`
3. Register tool metadata in route helper
4. Extend tool dispatcher logic
5. Add route + contract tests
6. Update README + architecture docs

## 16. Known Design Trade-offs

1. Single service process simplifies development but increases blast radius
2. Legacy compatibility endpoints add complexity but improve interoperability
3. Conservative timeout defaults improve responsiveness but may cut off slow sites

## 17. Future Architecture Roadmap

1. Add structured metrics and tracing
2. Introduce stricter fetch security policy
3. Add cache layer for frequent queries
4. Consider registry-based dynamic tool dispatch
5. Split route modules as tool count increases

## 18. Summary

The architecture is intentionally practical:

1. Clear separation of route, schema, service, and config layers
2. MCP-first transport support with compatibility paths
3. Timeout-bounded external dependency calls
4. Testable and extensible structure for growth

This design keeps the project beginner-friendly while still supporting production-style operational behavior.
