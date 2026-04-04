# Operations Runbook

This document defines production operations and incident handling for the MCP Web Search Server.

## 1. Service Critical Paths

Critical user paths:

1. MCP initialize (POST /mcp method initialize)
2. Tool discovery (POST /mcp method tools/list)
3. Tool execution (POST /mcp method tools/call)

Secondary paths:

1. Health endpoint
2. Legacy compatibility endpoints

## 2. On-Call Triage Sequence

When an issue is reported:

1. Check /health
2. Check initialize
3. Check tools/list
4. Check tools/call with a simple query
5. Inspect logs for timeouts/errors

## 3. Incident Severity

1. Sev-1: total outage or all MCP calls failing
2. Sev-2: major degradation, tool execution mostly failing
3. Sev-3: intermittent failures or elevated latency
4. Sev-4: minor bug or low-impact issue

## 4. Fast Diagnostic Commands

Health:
```bash
curl https://mcp-web-search-nwgd.onrender.com/health
```

Initialize:
```bash
curl -X POST https://mcp-web-search-nwgd.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

Tools list:
```bash
curl -X POST https://mcp-web-search-nwgd.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

Tool call:
```bash
curl -X POST https://mcp-web-search-nwgd.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"web_search","arguments":{"query":"status check","num_results":1}}}'
```

## 5. Failure Playbooks

### Playbook A: Failed to get tools

Symptoms:
1. Client connects but tools cannot be discovered

Actions:
1. Run tools/list diagnostic call
2. Verify response includes tools and inputSchema
3. Check recent route/schema changes
4. Deploy hotfix if contract mismatch found

### Playbook B: Timeout errors

Symptoms:
1. tool calls exceed expected response times

Actions:
1. verify SEARCH_TIMEOUT, FETCH_TIMEOUT, MCP_REQUEST_TIMEOUT
2. inspect logs for upstream latency
3. test minimal query and simple URL
4. if needed, temporarily reduce payload depth or num_results defaults

### Playbook C: Search failures only

Symptoms:
1. web_search fails, fetch_page works

Actions:
1. test DuckDuckGo call path with route test or service test
2. inspect warnings in search service logs
3. verify dependency package compatibility

### Playbook D: Fetch failures only

Symptoms:
1. fetch_page errors increase

Actions:
1. verify outbound network behavior
2. test known good URL (https://example.com)
3. inspect timeout and HTTP error logs

## 6. Observability Baseline

Minimum operational signals:

1. request success/failure counts
2. timeout counts by tool
3. p95 latency for tools/call
4. health endpoint uptime

## 7. Escalation

Escalate when:

1. Sev-1 persists > 10 minutes
2. Sev-2 persists > 30 minutes
3. rollback does not restore behavior

## 8. Post-Incident Template

1. Summary
2. Impact window
3. Root cause
4. Immediate fix
5. Long-term prevention
6. Tests/docs updated

## 9. Operational Hygiene

Weekly:
1. smoke test live MCP flow
2. review logs for error trends

Monthly:
1. dependency update review
2. timeout defaults review
3. documentation drift check
