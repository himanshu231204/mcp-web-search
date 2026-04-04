# Deployment Runbook

This runbook defines how to deploy and verify the MCP Web Search Server.

## 1. Deployment Targets

1. Local development
2. Docker
3. Render cloud deployment

## 2. Local Deployment

### Prerequisites

1. Python 3.11+
2. pip

### Steps

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run server:
```bash
python -m app.main
```

3. Verify health:
```bash
curl http://localhost:10000/health
```

4. Verify initialize:
```bash
curl -X POST http://localhost:10000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

## 3. Docker Deployment

### Build image

```bash
docker build -t mcp-web-search .
```

### Run container

```bash
docker run -p 10000:10000 mcp-web-search
```

### Verify

1. GET /health
2. POST /mcp initialize
3. POST /mcp tools/list

## 4. Render Deployment

Render config is defined in render.yaml.

### Required settings

1. Build command: pip install -r requirements.txt
2. Start command: uvicorn app.main:app --host 0.0.0.0 --port 10000

### Recommended environment variables

1. SEARCH_TIMEOUT=10
2. FETCH_TIMEOUT=10
3. MCP_REQUEST_TIMEOUT=25
4. SSE_HEARTBEAT_INTERVAL=5
5. MAX_CONTENT_LENGTH=5000

### Deploy verification checklist

1. GET /health returns healthy
2. POST /mcp initialize returns jsonrpc result
3. POST /mcp tools/list returns tools with inputSchema
4. POST /mcp tools/call web_search returns success
5. OpenCode command "opencode mcp list" shows connected

## 5. Post-Deploy Smoke Tests

Run immediately after deployment:

1. Health check:
```bash
curl https://mcp-web-search-nwgd.onrender.com/health
```

2. Initialize check:
```bash
curl -X POST https://mcp-web-search-nwgd.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

3. Tool list check:
```bash
curl -X POST https://mcp-web-search-nwgd.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

## 6. Rollback Procedure

If deployment is broken:

1. Confirm failure in smoke tests
2. Roll back to previous Render deploy
3. Re-run smoke tests
4. Open incident entry in maintenance notes

## 7. Common Deployment Failures

### Failure: Server reachable but MCP client cannot get tools

Likely cause:
- tools/list contract mismatch

Action:
- validate tools/list response shape and key casing (inputSchema)

### Failure: Timeout at 30s

Likely causes:
1. upstream latency spike
2. missing timeout config
3. deployment cold start

Action:
1. verify timeout env vars
2. check logs for timeout warnings
3. verify tool call latency

### Failure: CI green, runtime broken

Likely cause:
- environment drift

Action:
1. compare local and production env values
2. re-run smoke scripts directly against deployment URL

## 8. Deployment Readiness Checklist

Before release:

1. black --check app/ passes
2. pytest passes
3. README and API docs updated
4. render config validated
5. rollback plan known
