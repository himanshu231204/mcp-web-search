# Technical Documentation Index

This index provides a complete map of technical documentation for the MCP Web Search Server.

## Core Documents

1. [README.md](../README.md)
- Product overview, quick start, endpoint summary, and basic setup.

2. [ARCHITECTURE.md](../ARCHITECTURE.md)
- System architecture, component boundaries, request flows, and design trade-offs.

3. [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md)
- Internal development conventions, module behavior, and extension patterns.

4. [HOW_TO_BUILD_THE_MCP_SERVER.md](../HOW_TO_BUILD_THE_MCP_SERVER.md)
- Full beginner-to-advanced handbook for building, scaling, and operating MCP servers.

## Operational and Engineering Docs

1. [API_REFERENCE.md](API_REFERENCE.md)
- Route-by-route API contract details, JSON-RPC methods, and response formats.

2. [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md)
- Local, Docker, and Render deployment procedures with verification steps.

3. [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md)
- Incident handling, monitoring checks, and production troubleshooting playbooks.

4. [TESTING_GUIDE.md](TESTING_GUIDE.md)
- Test architecture, local commands, CI alignment, and contract testing guidance.

5. [SECURITY_MODEL.md](SECURITY_MODEL.md)
- Threat model, security controls, and hardening recommendations.

6. [MAINTENANCE_CHECKLIST.md](MAINTENANCE_CHECKLIST.md)
- Repeatable checklists for releases, post-deploy validation, and routine maintenance.

7. [CHANGELOG_DOCS.md](CHANGELOG_DOCS.md)
- Documentation change history and update template.

## CI/CD Documentation

1. [GITHUB_ACTIONS_SETUP.md](../GITHUB_ACTIONS_SETUP.md)
- GitHub Actions setup and quick start for lint, test, and deployment workflows.

## Recommended Reading Order

1. Start with [README.md](../README.md)
2. Read [ARCHITECTURE.md](../ARCHITECTURE.md)
3. Follow [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md)
4. Use [API_REFERENCE.md](API_REFERENCE.md) while implementing or integrating
5. Use runbooks and checklists for deployment and operations

## Documentation Ownership

When technical behavior changes, update the relevant documents in this order:

1. API contract change -> [API_REFERENCE.md](API_REFERENCE.md)
2. Code structure change -> [ARCHITECTURE.md](../ARCHITECTURE.md) and [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md)
3. Deployment change -> [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md)
4. Reliability/security change -> [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) and [SECURITY_MODEL.md](SECURITY_MODEL.md)
5. Process/checklist change -> [MAINTENANCE_CHECKLIST.md](MAINTENANCE_CHECKLIST.md)
