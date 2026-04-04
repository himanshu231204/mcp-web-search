# Testing Guide

This guide describes testing strategy and commands for the MCP Web Search Server.

## 1. Test Scope

Current suites:

1. Route tests: tests/test_routes.py
2. Service tests: tests/test_services.py

Primary goals:

1. Validate MCP protocol behavior
2. Validate tool behavior and resilience
3. Catch schema regressions early

## 2. Local Setup

Install dependencies:

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx
```

## 3. Run Tests

Run all tests:

```bash
pytest -q
```

Run route tests only:

```bash
pytest tests/test_routes.py -q
```

Run service tests only:

```bash
pytest tests/test_services.py -q
```

## 4. Critical Contract Tests

Always keep tests for:

1. initialize response shape
2. tools/list response includes inputSchema in MCP mode
3. tools/call returns stable result wrapper
4. unknown method returns JSON-RPC method-not-found error

These tests prevent client integration regressions.

## 5. Recommended Test Layers

1. Unit tests: helper and transformation logic
2. Route tests: endpoint and protocol contracts
3. Integration tests: route-to-service wiring with mocks
4. Optional smoke tests: live deployment checks

## 6. Flakiness Guidance

Avoid flaky tests by:

1. mocking external dependencies where practical
2. avoiding strict assertions on external webpage content wording
3. focusing on response shape and expected keys

## 7. CI Parity Checks

Before opening a PR, run:

```bash
black --check app/
ruff check app/
pytest -q
```

## 8. Adding Tests for New Tools

When adding a tool:

1. Add happy-path test
2. Add input-validation test
3. Add timeout/error-path test
4. Add MCP tools/list contract assertion for schema presence

## 9. Troubleshooting Test Failures

Common patterns:

1. Schema mismatch after route changes
2. Timeout defaults changed without test update
3. Unformatted code failing CI before tests run

Resolution path:

1. read failing assertion carefully
2. confirm expected contract in API docs
3. fix code or test expectation based on intended public behavior
