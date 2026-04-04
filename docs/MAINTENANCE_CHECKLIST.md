# Maintenance Checklist

This checklist provides repeatable maintenance routines for this repository.

## 1. Pre-Commit Checklist

1. black --check app/
2. ruff check app/
3. pytest -q
4. update docs for behavior changes

## 2. Pre-Release Checklist

1. Verify MCP initialize works
2. Verify tools/list works and includes expected schema keys
3. Verify tools/call works for both tools
4. Verify README + API_REFERENCE are current
5. Confirm deployment env vars are set

## 3. Post-Deploy Checklist

1. GET /health returns healthy
2. POST /mcp initialize succeeds
3. POST /mcp tools/list succeeds
4. POST /mcp tools/call web_search succeeds
5. OpenCode mcp list shows connected

## 4. Weekly Checklist

1. Review error logs and timeout trends
2. Re-run smoke checks against deployed URL
3. Confirm docs still match production behavior

## 5. Monthly Checklist

1. Review dependencies and update where safe
2. Validate CI workflow health and execution times
3. Revisit timeout and content limits based on observed traffic

## 6. Change-Type Checklist

### If MCP route behavior changes

1. update tests/test_routes.py
2. update docs/API_REFERENCE.md
3. update README examples if user-facing behavior changed

### If service behavior changes

1. update tests/test_services.py
2. update DEVELOPER_GUIDE.md
3. update architecture notes if component boundaries changed

### If deployment behavior changes

1. update docs/DEPLOYMENT_RUNBOOK.md
2. update GITHUB_ACTIONS_SETUP.md if CI/CD is affected

## 7. Incident Follow-Up Checklist

1. write incident summary
2. identify root cause
3. add prevention test or guardrail
4. update runbook section for recurring pattern

## 8. Documentation Hygiene Checklist

1. Keep docs/TECHNICAL_DOCUMENTATION_INDEX.md current
2. Remove stale references
3. Ensure all major docs are linked from README
