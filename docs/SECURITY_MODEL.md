# Security Model

This document defines security considerations and controls for the MCP Web Search Server.

## 1. Security Objectives

1. Protect service availability
2. Prevent unsafe external fetch behavior
3. Limit abuse through bounded execution
4. Avoid leaking sensitive data in logs/responses

## 2. Threat Surface

1. Untrusted client requests to MCP endpoints
2. Untrusted URLs passed to fetch_page
3. Potential high-volume request abuse
4. Third-party dependency risks

## 3. Current Controls

1. Input validation via Pydantic models
2. Timeouts on search/fetch/tool execution paths
3. Maximum content length enforcement
4. Controlled JSON-RPC error responses

## 4. Security Risks to Address Further

1. SSRF risk in unrestricted URL fetching
2. Missing explicit rate limiting in production path
3. Broad CORS policy for all origins

## 5. Recommended Hardening Plan

### Phase 1 (high priority)

1. Enforce URL scheme allowlist (http/https)
2. Block localhost and private/internal network targets where possible
3. Add request rate limiting middleware

### Phase 2 (medium priority)

1. Add request size limits
2. Add structured log redaction
3. Add suspicious-traffic alerting

### Phase 3 (longer-term)

1. Authentication for protected deployments
2. Usage quotas per client identity
3. Security regression tests

## 6. Logging and Data Handling

Guidelines:

1. Log error class and context, not full sensitive payloads
2. Avoid logging full scraped content in error paths
3. Keep retention windows appropriate for environment

## 7. Dependency Safety

1. Review dependency updates regularly
2. Address deprecation and vulnerability warnings promptly
3. Re-run test suite after dependency upgrades

## 8. Incident Response Triggers

Trigger security review when:

1. unusual traffic spikes occur
2. repeated fetch failures to internal-like targets are observed
3. dependency vulnerability notices affect runtime libraries

## 9. Security Checklist for New Tools

Before releasing any new tool:

1. validate input bounds
2. define timeout behavior
3. define safe error outputs
4. add abuse-case tests
5. update this security model if threat surface changes
