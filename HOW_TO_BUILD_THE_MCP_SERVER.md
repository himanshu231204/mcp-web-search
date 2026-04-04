# How to Build This MCP Server

[![MCP](https://img.shields.io/badge/MCP-Streamable_HTTP-blue)](https://modelcontextprotocol.io/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production-009688)](https://fastapi.tiangolo.com/)
[![Docs](https://img.shields.io/badge/Guide-Beginner_to_Advanced-brightgreen)](HOW_TO_BUILD_THE_MCP_SERVER.md)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## Credits

Primary author and maintainer credit for this handbook and project customization:

- Himanshu (`himanshu231204`)
- GitHub: https://github.com/himanshu231204
- LinkedIn: https://www.linkedin.com/in/himanshu231204
- Twitter (X): https://x.com/himanshu231204

## Table of Contents

1. [What You Are Building](#what-you-are-building)
2. [Core Concepts You Need to Understand](#core-concepts-you-need-to-understand)
3. [Project Structure](#project-structure)
4. [How the Server Starts](#how-the-server-starts)
5. [Why Configuration Matters](#why-configuration-matters)
6. [Designing the Data Models](#designing-the-data-models)
7. [The MCP Route Layer](#the-mcp-route-layer)
8. [Building the Search Service](#building-the-search-service)
9. [Building the Scraper Service](#building-the-scraper-service)
10. [Timeouts Are Not Optional](#timeouts-are-not-optional)
11. [How MCP Works in This Project](#how-mcp-works-in-this-project)
12. [Why the Repository Uses Both MCP and Legacy REST Endpoints](#why-the-repository-uses-both-mcp-and-legacy-rest-endpoints)
13. [How to Extend the Server With a New Tool](#how-to-extend-the-server-with-a-new-tool)
14. [How to Think About Error Handling](#how-to-think-about-error-handling)
15. [How to Test the Server](#how-to-test-the-server)
16. [Deploying the Server](#deploying-the-server)
17. [Beginner Mental Model for Building the Server Yourself](#beginner-mental-model-for-building-the-server-yourself)
18. [Example Walkthrough: A Full Search Request](#example-walkthrough-a-full-search-request)
19. [Example Walkthrough: A Full Page Fetch Request](#example-walkthrough-a-full-page-fetch-request)
20. [Common Beginner Mistakes](#common-beginner-mistakes)
21. [How This Project Solved Its Real MCP Issue](#how-this-project-solved-its-real-mcp-issue)
22. [Practical Advice for Beginners](#practical-advice-for-beginners)
23. [Summary of the Build Process](#summary-of-the-build-process)
24. [File Map for This Project](#file-map-for-this-project)
25. [Final Takeaway](#final-takeaway)
26. [Part II: Deep Internal Architecture](#part-ii-deep-internal-architecture)
27. [Protocol Engineering: JSON-RPC and MCP Semantics](#protocol-engineering-json-rpc-and-mcp-semantics)
28. [Production Security Blueprint for MCP Servers](#production-security-blueprint-for-mcp-servers)
29. [Reliability Engineering and Failure Modes](#reliability-engineering-and-failure-modes)
30. [Observability: Logs, Metrics, Traces, and Runbooks](#observability-logs-metrics-traces-and-runbooks)
31. [Testing Strategy: From Unit Tests to Contract Tests](#testing-strategy-from-unit-tests-to-contract-tests)
32. [CI/CD and Release Management](#cicd-and-release-management)
33. [Scaling Patterns and Performance Tuning](#scaling-patterns-and-performance-tuning)
34. [Advanced Tool Design Patterns](#advanced-tool-design-patterns)
35. [Complete Troubleshooting Encyclopedia](#complete-troubleshooting-encyclopedia)
36. [Learning Roadmap: 30-60-90 Day Plan](#learning-roadmap-30-60-90-day-plan)
37. [Glossary](#glossary)
38. [Final Credits and Acknowledgments](#final-credits-and-acknowledgments)

This guide explains how to build the MCP Web Search Server in a way that is friendly to beginners while still being useful for someone who wants to understand the design decisions behind the project. The goal is not just to show the final code, but to explain how the pieces fit together, why they exist, and how you can extend the server safely.

The project in this repository is a FastAPI-based Model Context Protocol server that exposes two capabilities:

1. Web search using DuckDuckGo.
2. Web page fetching and content extraction.

The main server entry point is [app/main.py](app/main.py), the MCP transport and tool routing logic lives in [app/routes/mcp.py](app/routes/mcp.py), the search logic is in [app/services/search.py](app/services/search.py), and the page scraping logic is in [app/services/scraper.py](app/services/scraper.py).

If you are new to MCP, the simplest way to think about it is this: an MCP server is a small network service that tells an AI client what tools it can use, how those tools should be called, and what results they return. In this project, the server lets a client ask for a search query or a web page fetch without the client having to implement those details itself.

---

## What You Are Building

Before writing code, it helps to understand the target system at a high level.

This server does four jobs:

1. It starts an HTTP application with FastAPI.
2. It exposes MCP-compatible endpoints for discovery and tool execution.
3. It calls out to external systems, such as DuckDuckGo and remote web pages.
4. It protects itself with timeouts and clean error handling so a slow upstream service does not freeze the whole server.

The overall flow is simple:

1. A client connects to the MCP endpoint.
2. The server returns its capabilities.
3. The client asks what tools are available.
4. The client calls one of the tools.
5. The server runs the tool and returns the result.

In this repository, the live MCP endpoint is `POST /mcp`, and a compatibility SSE stream is available at `GET /mcp`. The legacy REST endpoints under `/mcp/tools/*` still exist for direct access, but the primary MCP flow is now JSON-RPC over Streamable HTTP.

---

## Core Concepts You Need to Understand

To build this kind of server, you need a few basic concepts. You do not need to be an expert in all of them, but you should know what each one does.

### 1. HTTP Server

An HTTP server listens for requests from clients. In this project, FastAPI runs the HTTP server and handles routes like `/`, `/health`, and `/mcp`.

### 2. FastAPI

FastAPI is a Python web framework that makes it easy to define request handlers, validate inputs, and generate responses. It works especially well with Pydantic models.

### 3. Pydantic Models

Pydantic models define structured data. In this project, they describe requests and responses such as search queries, page fetch requests, and JSON-RPC payloads. They are defined in [app/schemas/models.py](app/schemas/models.py).

### 4. MCP

Model Context Protocol is a standard way for AI clients to discover and call tools. The important idea is that the client does not need to know the implementation details of your tool. It only needs the tool name, schema, and response format.

### 5. Async I/O

This server is asynchronous. That means it can handle slow network operations without blocking the entire process. In practice, this matters for web search and page fetching because those operations depend on the network.

### 6. Timeouts

Timeouts are essential. If DuckDuckGo or a website is slow, the server should stop waiting after a reasonable period and return gracefully. Without timeouts, one bad request can make the server appear broken.

### 7. SSE

Server-Sent Events are a way to stream updates from server to client. This project keeps a compatibility SSE stream at `GET /mcp`, which is useful for older clients or fallback behavior.

---

## Project Structure

This repository follows a compact but clear structure:

```text
app/
  main.py
  core/
    config.py
  routes/
    mcp.py
  schemas/
    models.py
  services/
    search.py
    scraper.py
tests/
```

Here is what each part does:

### [app/main.py](app/main.py)

This file creates the FastAPI application, adds middleware, and includes the routers.

### [app/core/config.py](app/core/config.py)

This file stores environment-driven configuration values such as timeouts, port, and default result counts.

### [app/routes/mcp.py](app/routes/mcp.py)

This is the heart of the server. It defines MCP-compatible routes, the SSE compatibility stream, and the REST routes for search and fetch.

### [app/schemas/models.py](app/schemas/models.py)

This file contains Pydantic models that validate requests and responses.

### [app/services/search.py](app/services/search.py)

This service calls DuckDuckGo and converts the search results into a format the server can return.

### [app/services/scraper.py](app/services/scraper.py)

This service fetches a page, parses HTML, removes scripts and styles, and extracts readable content.

### [tests/](tests/)

This folder contains route and service tests that verify the server behaves correctly.

---

## How the Server Starts

The application entry point is [app/main.py](app/main.py). It does three important things.

First, it loads configuration from [app/core/config.py](app/core/config.py). Second, it creates the FastAPI app. Third, it includes the MCP router so the app knows about the routes defined in [app/routes/mcp.py](app/routes/mcp.py).

Here is the conceptual flow:

1. Python imports `app.main`.
2. `get_config()` reads environment variables and fills defaults.
3. FastAPI is created with the app metadata.
4. CORS middleware is added.
5. The MCP router is mounted under `/mcp`.
6. The health and root endpoints are added.

This structure matters because a clean startup path makes the server easier to debug and deploy. If the app fails to load, you know the problem is probably in import-time code or configuration.

### Example from this project

In [app/main.py](app/main.py), the MCP routers are included like this:

```python
app.include_router(mcp.mcp_router, prefix="/mcp")
app.include_router(mcp.router, prefix="/mcp")
app.include_router(mcp.exec_router, prefix="/mcp")
```

That means a single route file handles three related concerns:

1. MCP root behavior.
2. Tool listing and execution.
3. Streaming execution endpoints.

This is reasonable for a small project because the functionality is tightly related. If the project grows, you could split these routes into separate modules.

---

## Why Configuration Matters

Beginner projects often hard-code values like timeout durations, ports, or default limits. That works at first, but it becomes painful when deploying to different environments.

This project uses [app/core/config.py](app/core/config.py) to centralize settings.

### What the config does

The config controls:

1. Server host and port.
2. Default search result counts.
3. Fetch timeout.
4. Search timeout.
5. MCP request timeout.
6. SSE heartbeat interval.

### Why it matters

Different environments have different behavior. For example:

1. Local development may be fast and stable.
2. Render may have cold starts or slower network paths.
3. A real website may respond slowly or block bots.

If you keep timeouts in one place, you can tune them without touching the business logic.

### Example from this project

The server uses these settings:

- `SEARCH_TIMEOUT` for DuckDuckGo search calls.
- `FETCH_TIMEOUT` for HTTP page fetches.
- `MCP_REQUEST_TIMEOUT` to protect the overall tool call path.
- `SSE_HEARTBEAT_INTERVAL` to keep the compatibility stream alive.

This makes the server easier to run locally and more stable in deployment.

---

## Designing the Data Models

One of the most important skills in backend development is defining the shape of your data clearly.

In this project, the Pydantic models in [app/schemas/models.py](app/schemas/models.py) act as the contract between the client and server.

### Why models are useful

Models help you:

1. Validate input early.
2. Document your API.
3. Avoid ad hoc dictionaries scattered through the code.
4. Make tests easier to write.

### Existing models in this project

The code defines models for:

1. Search requests and responses.
2. Page fetch requests and responses.
3. Tool lists.
4. Tool execution requests.
5. JSON-RPC requests and responses.

### Beginner-friendly explanation

If a client wants to search the web, it sends a request that looks like:

```json
{
  "query": "python async programming",
  "num_results": 5
}
```

The `WebSearchRequest` model checks that `query` exists and is not empty, and that `num_results` stays within a valid range.

If the client wants to fetch a page, it sends:

```json
{
  "url": "https://example.com"
}
```

The `FetchPageRequest` model makes sure the field is present.

### MCP-specific models

The MCP JSON-RPC request model is important because it defines how the server understands protocol messages. This project added a `JSONRPCRequest` model so the `/mcp` endpoint can validate methods like `initialize` and `tools/list`.

That is the right place to model protocol messages because it keeps the route code simple. Instead of manually parsing everything from raw JSON, the route can receive a structured object.

---

## The MCP Route Layer

The most important file in the repository is [app/routes/mcp.py](app/routes/mcp.py). If you understand this file, you understand the shape of the whole server.

It handles three concerns:

1. Primary MCP JSON-RPC traffic.
2. SSE compatibility traffic.
3. Legacy REST endpoints for direct use.

### The primary MCP endpoint

The real MCP entry point is `POST /mcp`.

This endpoint accepts JSON-RPC messages such as:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```

The server responds with capabilities and server info.

This is the first thing an MCP client expects. If the initialize step is wrong, the whole connection sequence can fail, even if the rest of your routes are fine.

### The SSE compatibility endpoint

The `GET /mcp` endpoint returns an SSE stream. It is mainly a compatibility bridge.

The stream begins with an `endpoint` event, then sends a connection acknowledgement, and continues emitting heartbeat messages.

Why keep it?

1. Some clients or tools still use legacy fallback behavior.
2. It gives older integrations a path to connect.
3. It provides a visible stream for diagnostics.

### Tool listing

The `tools/list` JSON-RPC method returns the list of available tools in MCP format. In this project, that list contains `web_search` and `fetch_page`.

The important detail is that the response must be protocol-compliant. That is why the route returns `inputSchema` rather than `input_schema` for MCP responses.

### Tool execution

The `tools/call` method is where real work happens.

The request includes:

1. The tool name.
2. The arguments for that tool.

The route looks up the tool, validates the arguments through the surrounding models and services, calls the service, and returns the result.

### Why the route layer is thin

The route layer should not do all the work itself. Its job is to:

1. Parse the request.
2. Select the right service.
3. Enforce timeouts and return errors.
4. Convert results into protocol responses.

That keeps the code easier to understand and easier to test.

### Example from this project

When `tools/call` is used for `web_search`, the route eventually calls the search service, which calls DuckDuckGo. When `tools/call` is used for `fetch_page`, the route calls the scraper service, which fetches and parses a webpage.

That separation is intentional:

1. Routes handle protocol and HTTP details.
2. Services handle domain logic.
3. Schemas handle validation.

This is a very common and healthy backend design pattern.

---

## Building the Search Service

The web search service is in [app/services/search.py](app/services/search.py).

Its job is simple:

1. Ask DuckDuckGo for results.
2. Convert those results into a normalized list of dictionaries.
3. Return an empty list if the search fails.

### Why a service layer helps

If all search logic lived inside the route, the route would become harder to read and harder to test. A service layer keeps the search implementation isolated.

### Async design

Searching is network-bound work. Instead of blocking the event loop, the code uses async patterns. The DuckDuckGo call runs inside `asyncio.to_thread()`, and then the whole operation is wrapped with `asyncio.wait_for()`.

This means:

1. The blocking library call is moved out of the main async loop.
2. The request cannot run forever.
3. The server stays responsive even when external services are slow.

### Example from this project

The service returns items like:

```json
{
  "title": "Example Title",
  "url": "https://example.com",
  "snippet": "A short summary of the page"
}
```

That format is simple and stable. It is easy for MCP clients and REST clients to consume.

### Error handling philosophy

This project follows a practical rule: services should fail safely.

If DuckDuckGo fails, the search service logs the error and returns an empty list. That is better than crashing the whole server. In a tool server, a graceful empty result is often more useful than a hard exception.

---

## Building the Scraper Service

The page fetch logic is in [app/services/scraper.py](app/services/scraper.py).

Its job is to fetch a webpage and extract readable content.

### What the scraper does

1. Sends an HTTP GET request.
2. Follows redirects.
3. Parses the HTML with BeautifulSoup.
4. Removes script and style tags.
5. Extracts the title and visible text.
6. Truncates content if it is too long.

### Why this is useful

Many AI tools need the content of a page, not just the URL. A scraper turns raw HTML into useful text that can be summarized or analyzed.

### Example from this project

If the client fetches `https://example.com`, the scraper may return something like:

```json
{
  "title": "Example Domain",
  "content": "Example Domain This domain is for use in illustrative examples...",
  "url": "https://example.com"
}
```

That is much more useful to an AI client than raw HTML.

### Why timeouts matter here

Web pages are unpredictable. Some sites are fast, some are slow, and some are broken. If the scraper waits too long, the whole MCP request can fail. That is why the project uses a timeout in the HTTP client.

### Practical design choice

The scraper also returns friendly fallback content on failure, such as a timeout message or HTTP error description. This is useful because the caller still gets a structured response instead of a crash.

---

## Timeouts Are Not Optional

If you are building a server that depends on the network, timeouts are one of the most important design decisions you will make.

This project uses timeouts in three places:

1. Search timeout.
2. Fetch timeout.
3. MCP request timeout.

### Why the project needed this

The original failure mode was that the deployment could time out at the client side even though the server was alive. That happened because some parts of the request path could wait too long.

The fix was to bound the time spent on external work.

### Beginner rule of thumb

If your endpoint depends on something outside your control, wrap it in a timeout.

That applies to:

1. Search APIs.
2. Web page fetching.
3. Database calls.
4. Third-party services.
5. Long-running file operations.

### Example from this project

The route layer now protects the tool call path with `MCP_REQUEST_TIMEOUT`. The service layer protects DuckDuckGo with `SEARCH_TIMEOUT` and the page fetch with `FETCH_TIMEOUT`.

That means the server can return an error or empty result quickly instead of hanging until the platform kills the request.

---

## How MCP Works in This Project

MCP can look abstract when you first meet it, but the idea becomes simple if you break it down.

The client and server follow a short protocol:

1. Initialize.
2. Discover tools.
3. Call a tool.
4. Receive results.

### Step 1: Initialize

The client sends `initialize` to `POST /mcp`.

The server replies with:

1. Protocol version.
2. Capabilities.
3. Server info.

### Step 2: List tools

The client sends `tools/list`.

The server returns the available tools and their input schemas.

### Step 3: Call a tool

The client sends `tools/call` with the tool name and arguments.

The server executes the tool and returns structured output.

### Step 4: Handle errors gracefully

If the method is not found, the server returns a JSON-RPC error.
If the tool times out, the server returns a tool timeout error.
If input is missing, the server returns a validation error.

### Example from this project

The server now returns MCP-compliant tool definitions with `inputSchema` because clients expect that exact field name.

That may seem like a small detail, but in protocol design, exact field names matter.

---

## Why the Repository Uses Both MCP and Legacy REST Endpoints

At first glance, it may seem redundant to keep both MCP JSON-RPC routes and direct REST routes like `/mcp/tools/web_search`.

There are good reasons to keep both.

### 1. Compatibility

Existing users may already call the REST endpoints directly.

### 2. Testing

REST endpoints are easy to test with standard HTTP tools.

### 3. Debugging

If something goes wrong with the MCP transport, the REST route can help isolate whether the problem is in the tool logic or the protocol layer.

### 4. Incremental migration

You can migrate clients to MCP without forcing everyone to switch at once.

### Example from this project

The MCP route and the REST route both use the same service layer underneath. That is the right design because it avoids duplicating the business logic.

---

## How to Extend the Server With a New Tool

Once you understand the pattern, adding a new tool is straightforward.

Suppose you want to add `image_search`.

### Step 1: Define the schema

Add request and response models in [app/schemas/models.py](app/schemas/models.py).

### Step 2: Implement the service

Create a service in [app/services/](app/services/) that performs the actual work.

### Step 3: Register the tool

Add the tool to the tool list in [app/routes/mcp.py](app/routes/mcp.py).

### Step 4: Add dispatch logic

Teach the route layer how to call the new service when the tool name is selected.

### Step 5: Add tests

Update [tests/test_routes.py](tests/test_routes.py) and add service tests if needed.

### Step 6: Update documentation

Add the new tool to [README.md](README.md) and, if relevant, [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).

### Why this structure works

This pattern gives you a repeatable process. Every tool has:

1. A schema.
2. A service.
3. A route entry.
4. A test.
5. A doc entry.

That is exactly how maintainable backend systems are built.

---

## How to Think About Error Handling

Error handling is not just about exceptions. It is about making sure the user gets something useful when things go wrong.

This project uses several error-handling strategies.

### Validation errors

If a required field is missing, FastAPI and Pydantic return a 422 response automatically.

### Timeout errors

If a search or fetch takes too long, the server returns a controlled timeout response.

### Unknown method errors

If the client calls a JSON-RPC method that does not exist, the MCP route returns a method-not-found error.

### External service errors

If DuckDuckGo or a web page fails, the services log the error and return a fallback value.

### Why this is the right approach

Tool servers should be resilient. The client should be able to ask for a tool and get a deterministic response shape even if the tool itself fails.

That makes the system easier to integrate and easier to debug.

---

## How to Test the Server

Testing is where you prove that the design works.

The repository already includes tests in [tests/test_routes.py](tests/test_routes.py) and [tests/test_services.py](tests/test_services.py).

### What the tests cover

They check:

1. Root and health endpoints.
2. Tool listing.
3. Search and fetch validations.
4. MCP initialize.
5. MCP tools/list.
6. MCP tools/call.
7. SSE compatibility event order.

### Why these tests matter

Each one protects a part of the server that is easy to break when making changes.

For example:

1. If you change the tool schema format, MCP clients may fail.
2. If you remove a timeout, the server may hang.
3. If you change the SSE stream format, compatibility clients may stop connecting.

### Example from this project

The test suite is especially important because the project had a real integration issue where the client reported “Failed to get tools.” The tests now help catch schema mismatches like that earlier.

---

## Deploying the Server

The project can be deployed to Render using `render.yaml` and the app entry point.

### Deployment basics

When deploying, you need to make sure:

1. The app starts on the expected host and port.
2. The environment variables are set correctly.
3. The process can answer MCP requests quickly enough.

### What to watch for

Common deployment issues include:

1. Request timeouts.
2. Incorrect tool schema format.
3. Missing environment variables.
4. Slow startup.
5. Cold start delays.

### Example from this project

The server now exposes a `/health` endpoint and a `/mcp` endpoint that can be checked independently. That makes deployment troubleshooting easier.

If OpenCode can reach `/health` but not `mcp list`, the problem is likely protocol shape rather than network availability.

---

## Beginner Mental Model for Building the Server Yourself

If you wanted to build this project from scratch, here is the mental model you should use.

### First: Build the simplest possible HTTP app

Start with FastAPI and add a root route and a health route.

### Second: Define the data shapes

Add Pydantic models for the inputs and outputs.

### Third: Write the services

Implement search and fetch as independent async service classes or functions.

### Fourth: Add the MCP protocol layer

Teach the server how to respond to initialize, tools/list, and tools/call.

### Fifth: Add timeouts and fallbacks

Make sure slow operations do not hang forever.

### Sixth: Add tests

Write tests for the endpoints, services, and protocol responses.

### Seventh: Document it

Write a README that explains how to run and use the server.

That sequence is important because it keeps the project understandable. If you try to do everything at once, the protocol details and service logic can become tangled.

---

## Example Walkthrough: A Full Search Request

Let us walk through a complete example using this project.

### Scenario

An MCP client wants to search for `python async programming`.

### Step 1: Initialize

The client sends an initialize request to `POST /mcp`.

### Step 2: Get tools

The client calls `tools/list`.

The server returns:

1. `web_search`
2. `fetch_page`

### Step 3: Call the search tool

The client sends `tools/call` with the `web_search` tool name and arguments.

### Step 4: Execute the search

The route layer calls the search service.

The search service calls DuckDuckGo and waits for results.

### Step 5: Return the result

The route wraps the returned list in MCP content format and sends it back to the client.

### What the client sees

The result contains a text payload that is still machine-readable. This is important because MCP clients often want both human-readable content and structured output.

---

## Example Walkthrough: A Full Page Fetch Request

Now let us walk through a page fetch.

### Scenario

The client wants content from `https://example.com`.

### Step 1: Call the fetch tool

The client sends `tools/call` with `fetch_page`.

### Step 2: Execute HTTP request

The route uses the scraper service to fetch the page.

### Step 3: Parse HTML

BeautifulSoup strips scripts and styles, then extracts readable text.

### Step 4: Return structured content

The server returns title, content, and URL.

### Why this is useful

This turns the web into something an AI tool can actually use. Instead of raw HTML, the client gets readable content that is easier to summarize, quote, or analyze.

---

## Common Beginner Mistakes

Here are mistakes people often make when building a server like this.

### 1. Putting all logic in one file

It is tempting to put everything in the route handler, but that quickly becomes hard to maintain.

### 2. Skipping validation

If you do not validate input, you get fragile code and confusing errors.

### 3. Ignoring timeouts

This is one of the fastest ways to make a server feel broken.

### 4. Returning inconsistent shapes

Clients rely on predictable response formats.

### 5. Forgetting protocol details

For MCP, field names and method names matter. A small mismatch can stop a client from connecting.

### 6. Not writing tests

Without tests, protocol regressions can sneak in during refactoring.

---

## How This Project Solved Its Real MCP Issue

This repository originally had a problem where the client could not get tools from the server.

The root cause was not that the server was offline. The server was reachable. The issue was that the MCP response format did not match what clients expected.

The solution was to make the JSON-RPC tool listing return the proper MCP schema field name and to ensure the initialize flow matched the client’s expectations.

That is an important lesson:

1. A server can be “up” but still fail a protocol handshake.
2. API shape matters as much as availability.
3. A good test suite should catch this before deployment.

For beginners, this is one of the most valuable things to learn. Most backend bugs are not dramatic crashes. They are mismatches in assumptions between components.

---

## Practical Advice for Beginners

If you are new to building MCP servers, use this project as a template, but do not copy it blindly.

### Start small

Begin with one tool.

### Test each layer separately

Test the service logic before testing the protocol layer.

### Keep routes thin

Let the route handle protocol details and let the service handle the actual work.

### Add timeouts early

Do not wait until deployment fails to add them.

### Document real examples

Examples are often more useful than abstract explanations.

### Use your tests as documentation

If a test is hard to understand, your design may be harder to understand than it should be.

---

## Summary of the Build Process

If you strip away the details, the build process looks like this:

1. Create a FastAPI app.
2. Add configuration.
3. Define data models.
4. Implement services.
5. Add MCP routes.
6. Add SSE compatibility.
7. Add timeouts.
8. Add tests.
9. Write documentation.
10. Deploy and verify.

That is the full mental model.

This repository already follows that pattern, which is why it is a good beginner example. You can see the separation of concerns clearly in the codebase, and you can trace a request from the HTTP layer down to the service layer and back.

---

## File Map for This Project

Use these files as your reference points while learning the server:

- [app/main.py](app/main.py)
- [app/core/config.py](app/core/config.py)
- [app/routes/mcp.py](app/routes/mcp.py)
- [app/schemas/models.py](app/schemas/models.py)
- [app/services/search.py](app/services/search.py)
- [app/services/scraper.py](app/services/scraper.py)
- [tests/test_routes.py](tests/test_routes.py)
- [tests/test_services.py](tests/test_services.py)

Each file covers one major part of the system. If you read them in that order, the design becomes easier to follow.

---

## Final Takeaway

The best way to understand this MCP server is to think of it as three layers:

1. The protocol layer, which speaks MCP.
2. The service layer, which does the work.
3. The data layer, which validates inputs and shapes outputs.

The protocol layer is in [app/routes/mcp.py](app/routes/mcp.py). The service layer is in [app/services/search.py](app/services/search.py) and [app/services/scraper.py](app/services/scraper.py). The data layer is in [app/schemas/models.py](app/schemas/models.py).

When those layers stay separate, the server is easier to understand, easier to test, and easier to extend.

That is the main lesson from this repository: a clean MCP server is not just about making requests succeed. It is about making the whole system understandable, reliable, and predictable for both humans and clients.

---

## Part II: Deep Internal Architecture

This section goes much deeper than the quick-start perspective. It explains the architecture as if you were preparing to maintain this server for years, onboard new contributors, and support multiple MCP clients with different behavior and expectations.

### Layered architecture in practical terms

In software architecture, many diagrams show three boxes and arrows. What matters more is whether each layer has a strict and understandable responsibility. In this project, you can think in six layers:

1. Transport layer: HTTP, JSON-RPC payloads, SSE events.
2. Protocol layer: MCP method routing and response shaping.
3. Validation layer: Pydantic models and request contracts.
4. Service layer: search and scrape implementations.
5. Platform layer: process model, deployment, runtime behavior.
6. Operations layer: observability, testing, CI/CD, and incident response.

If these layers are mixed carelessly, the code may still work for a while, but every change becomes risky. This is why [app/routes/mcp.py](app/routes/mcp.py) should not become a giant file full of scraping details, and [app/services/scraper.py](app/services/scraper.py) should not start producing JSON-RPC error objects directly.

### Architectural boundaries and anti-corruption rules

Healthy boundaries for this project:

1. Routes may depend on services and schemas.
2. Services may depend on configuration and third-party libraries.
3. Services should not depend on FastAPI-specific classes such as HTTPException.
4. Schemas should remain transport-neutral where possible.
5. Configuration should not import routes or services.

These rules stop circular dependencies and keep refactors possible. As an example, if you later support stdio transport in addition to HTTP, you can reuse the services without rewriting core logic.

### Why modularity matters more in MCP servers

MCP servers evolve quickly:

1. New tools are added.
2. Existing tools need stricter safety.
3. Client behavior changes as protocol support improves.
4. Deployment environments change from local to cloud.

When change is constant, modularity is a survival strategy, not a luxury.

---

## Protocol Engineering: JSON-RPC and MCP Semantics

Many beginners think of protocol handling as "just parse JSON and return JSON." In real systems, protocol correctness is a form of compatibility engineering. A tiny mismatch breaks clients even when endpoints are online.

### JSON-RPC fundamentals used by MCP

JSON-RPC messages include:

1. `jsonrpc`: usually `2.0`.
2. `id`: request correlation identifier.
3. `method`: operation name.
4. `params`: method input.
5. `result` or `error`: response payload.

In this project, [app/routes/mcp.py](app/routes/mcp.py) validates incoming requests and routes `initialize`, `notifications/initialized`, `tools/list`, and `tools/call`.

### Why method naming and field naming must be exact

Client parsers usually map method names and field names exactly. If your server returns `input_schema` while the client expects `inputSchema`, the client may fail to discover tools.

That exact issue happened in this project and was corrected by returning MCP-compliant `inputSchema` for JSON-RPC tool listing.

### Initialize handshake and capability declaration

The `initialize` response is not ceremonial. It tells clients:

1. Which protocol version the server implements.
2. Which capability groups exist.
3. How to identify the server in logs and UI.

If these details are absent or malformed, tool calls may never be attempted.

### Notifications and id-less messages

`notifications/initialized` is commonly sent without expecting a result payload. Your route should handle this path quickly and return acceptance semantics (such as 202) when appropriate.

### Tool call response shaping

A mature MCP response for tool execution usually has predictable content wrappers. This project returns text content carrying structured JSON. This approach keeps compatibility high across clients while still allowing richer future encodings.

### Protocol version strategy

Do not hardcode protocol assumptions everywhere. Keep protocol-version-related behavior centralized so you can evolve with future MCP revisions.

Good strategy:

1. Keep protocol version string in one place.
2. Add compatibility tests around `initialize` and `tools/list`.
3. Include protocol details in release notes when changed.

---

## Production Security Blueprint for MCP Servers

Security for an MCP tool server is not optional. A tool server can become a proxy to external systems and may process untrusted input.

### Security threat model for this project

Primary threats:

1. SSRF-like behavior in fetch tools.
2. Abuse through high request volume.
3. Oversized responses causing memory pressure.
4. Untrusted URLs and redirects.
5. Dependency vulnerabilities.

### URL safety policy for fetch tools

For `fetch_page`, enforce rules such as:

1. Allow only `http` and `https` schemes.
2. Block local and metadata IP ranges where possible.
3. Limit redirect chains.
4. Limit response size.
5. Set conservative timeouts.

Even if this project starts simple, documenting policy now helps future hardening.

### Input validation policy

Use Pydantic and explicit constraints:

1. Minimum and maximum string lengths.
2. Numeric bounds.
3. Required fields.

Reject unknown or malformed payloads early, before expensive network calls.

### Secret and credential policy

Even if your current tools do not use secrets:

1. Never log tokens.
2. Never commit secrets to Git.
3. Keep environment configuration separate from code.

### CORS and network exposure

If this is an internal server, avoid broad CORS defaults in production. In public deployments, document the risk profile and expected client population.

### Logging and privacy

Logs should be useful but privacy-aware. Consider masking user data where appropriate and avoid storing full scraped documents in error logs.

---

## Reliability Engineering and Failure Modes

Reliability is the ability to produce useful behavior under imperfect conditions.

### Typical failure categories in this server

1. Upstream search API instability.
2. Slow or malformed web pages.
3. Client disconnects during streaming.
4. Deployment cold starts.
5. Temporary DNS/network failures.

### Reliability design already present

This project includes several reliability features:

1. Timeouts at service and route levels.
2. Fallback responses for fetch/search failures.
3. Health endpoint for operational checks.
4. SSE heartbeat in compatibility stream.

### Recommended additional reliability patterns

1. Add retry policy only where safe and bounded.
2. Add circuit-breaker behavior for repeated upstream failures.
3. Add per-tool latency dashboards.
4. Add request IDs for traceability.

### Error budget thinking for beginners

You can define practical service goals such as:

1. 99 percent of tool list requests under 1 second.
2. 95 percent of search calls under 8 seconds.
3. 99 percent of fetch calls under 12 seconds.

These are not strict requirements in a learning project, but they are useful for building operational discipline.

---

## Observability: Logs, Metrics, Traces, and Runbooks

If you cannot observe behavior, you cannot operate or improve the system.

### Logging strategy

At minimum, log:

1. Route entry and exit for critical methods.
2. Tool name and coarse request size.
3. Timeout events.
4. External HTTP failures.
5. Unexpected exceptions.

Use structured logs where possible. Include fields such as method, tool name, duration, status, and request ID.

### Metrics to track

Useful starter metrics:

1. Request count by endpoint.
2. Error count by endpoint and error type.
3. Latency percentiles for each tool.
4. Timeout count by tool.
5. Active SSE connections.

### Tracing

Distributed tracing can be added later, but even local span-style timing helps. Track time spent in:

1. Parsing and validation.
2. Service dispatch.
3. External network call.
4. Response serialization.

### Runbook example for "Failed to get tools"

When users report MCP tool discovery failure:

1. Verify health endpoint.
2. Verify `initialize` response shape.
3. Verify `tools/list` response uses `inputSchema`.
4. Check logs for JSON-RPC method-not-found or validation errors.
5. Confirm latest deployment version is active.

This runbook now maps directly to lessons learned in this repository.

---

## Testing Strategy: From Unit Tests to Contract Tests

A one-stop MCP handbook should teach not only how to build but how to protect behavior over time.

### Test pyramid for this project

1. Unit tests for helpers and service transformations.
2. Route tests for protocol behavior.
3. Integration tests for network-dependent components with controlled mocks.
4. Contract tests to verify MCP payload structure.

### Contract tests are crucial for MCP

Protocol regressions often come from shape changes, not logic changes. Add tests that assert exact keys:

1. `initialize` includes protocol version and capabilities.
2. `tools/list` includes tool name, description, and `inputSchema`.
3. `tools/call` result wrapper shape remains stable.

### Suggested advanced tests

1. Batch JSON-RPC request handling (if implemented later).
2. Invalid method with and without `id`.
3. Large argument payload rejection.
4. Timeout path returns deterministic error code.

### Test data design

Keep fixtures realistic but bounded. For scraping tests, use stable pages such as `example.com` and keep assertions focused on structure rather than exact content wording.

---

## CI/CD and Release Management

A production learning project should treat CI as a quality gate.

### CI checks this project should include

1. Formatting check (Black).
2. Lint check (Ruff).
3. Test suite execution.
4. Optional type checking (Mypy).

### Why formatting failures matter

Formatting failures seem minor but cause noise, broken build confidence, and merge friction. This repository already experienced a CI Black failure in [app/routes/mcp.py](app/routes/mcp.py). The right fix was deterministic formatting alignment, not bypassing the check.

### Branch and release policy

Simple and effective flow:

1. Feature branch per change.
2. Pull request with tests.
3. CI green required.
4. Merge to main.
5. Auto-deploy and smoke test.

### Release checklist

Before release:

1. `black --check app/` passes.
2. Route tests pass.
3. MCP initialize and tools/list smoke tests pass on deployment URL.
4. README and guide reflect behavior.

---

## Scaling Patterns and Performance Tuning

Even small MCP servers can face bursty usage.

### Concurrency model basics

FastAPI with async handlers can process multiple requests concurrently, but CPU-bound work or blocking libraries can still stall throughput.

This is why wrapping blocking search calls with `asyncio.to_thread()` is important.

### Performance bottlenecks in this project

Likely bottlenecks:

1. External search API latency.
2. Slow remote websites for fetch.
3. Large HTML parsing overhead.
4. Serialization of large content payloads.

### Practical tuning options

1. Keep content length bounded.
2. Use per-tool timeout tuning.
3. Consider caching frequent search results.
4. Add connection pooling and keep-alive tuning.
5. Add rate limits for abusive traffic.

### Caching strategy for beginners

Start with small in-memory cache for hot queries. Document cache behavior clearly:

1. Cache key.
2. TTL.
3. Maximum entry count.
4. Invalidation behavior.

If cache correctness becomes complex, keep it out until requirements demand it.

---

## Advanced Tool Design Patterns

Beyond basic request-response tools, mature MCP servers often need richer behavior.

### Pattern 1: Tool composition

Compose tools internally. Example: search first, then fetch top result content. Keep this composition server-side if client simplicity is prioritized.

### Pattern 2: Argument normalization

Normalize tool arguments before service invocation. For example:

1. Trim query whitespace.
2. Clamp numeric bounds.
3. Validate URL scheme.

### Pattern 3: Deterministic output contracts

Return predictable shapes even on error. Include `isError` flags and concise messages.

### Pattern 4: Capability flags

Expose optional capabilities in initialize response so clients can adapt without hardcoding assumptions.

### Pattern 5: Compatibility adapters

Maintain adapters for legacy endpoints while moving toward canonical MCP paths.

This repository already demonstrates this with both JSON-RPC and compatibility routes.

---

## Complete Troubleshooting Encyclopedia

This section is designed as a practical checklist for real failures.

### Symptom: MCP server appears connected but no tools

Possible causes:

1. `tools/list` response key mismatch.
2. Incorrect method handling.
3. Invalid JSON-RPC response envelope.

Checks:

1. POST initialize manually.
2. POST tools/list manually.
3. Compare response keys against protocol expectations.

### Symptom: Client times out at 30 seconds

Possible causes:

1. Missing timeout wrappers.
2. Slow upstream network calls.
3. Deployment-level request ceiling.

Checks:

1. Confirm service timeouts are loaded from environment.
2. Confirm route-level timeout is active.
3. Confirm logs contain timeout warnings rather than hangs.

### Symptom: Search works locally but fails in deployment

Possible causes:

1. DNS differences.
2. outbound network policy.
3. dependency differences.

Checks:

1. Compare dependency versions.
2. Probe outbound HTTP from deployment shell if available.
3. Review runtime warnings in logs.

### Symptom: CI fails on formatting

Cause:

1. Unformatted Python source.

Fix:

1. Run Black locally.
2. Re-run CI.
3. Avoid mixing formatting and logic in giant commits.

### Symptom: SSE stream disconnects quickly

Possible causes:

1. Client not consuming stream.
2. Proxy buffering or idle timeout.
3. heartbeat interval too high.

Checks:

1. Verify heartbeat interval config.
2. Verify streaming headers.
3. Validate event ordering with a simple curl stream reader.

---

## Learning Roadmap: 30-60-90 Day Plan

If you are a beginner and want to truly master MCP server development, use this progression.

### Day 1 to 30: Foundations

Goals:

1. Understand HTTP request/response lifecycle.
2. Learn FastAPI routing and Pydantic validation.
3. Read [app/main.py](app/main.py) and [app/routes/mcp.py](app/routes/mcp.py) line by line.

Exercises:

1. Add a trivial tool that returns server time.
2. Add tests for it.
3. Document it in README.

### Day 31 to 60: Reliability and protocol confidence

Goals:

1. Understand JSON-RPC error semantics.
2. Implement better timeout handling and validation.
3. Add contract tests for tool schema.

Exercises:

1. Add tool input validation for URL safety.
2. Add timeout-specific test cases.
3. Add runbook entries for new failures.

### Day 61 to 90: Production hardening

Goals:

1. Add metrics and structured logging.
2. Add CI quality gates.
3. Add release checklist and operational playbook.

Exercises:

1. Add request ID propagation in logs.
2. Track per-tool latency metric stubs.
3. Run a lightweight load test and document results.

---

## Glossary

MCP: Model Context Protocol, a standard for exposing tools to AI clients.

JSON-RPC: A lightweight RPC format over JSON, used by MCP for method calls and responses.

SSE: Server-Sent Events, a one-way streaming protocol from server to client.

Transport: The communication mechanism carrying protocol messages, such as HTTP POST or SSE GET.

Schema: A formal description of data shape used for validation and interoperability.

Timeout: A maximum duration after which waiting work is aborted and handled as failure.

Contract test: A test asserting externally visible payload shape and semantics.

Compatibility route: Legacy endpoint maintained while migrating to preferred protocol paths.

---

## Final Credits and Acknowledgments

This handbook was expanded as a deep practical reference for beginners and intermediate engineers who want a one-stop guide to designing, implementing, operating, and evolving an MCP server.

Project and community credit:

1. Himanshu (`himanshu231204`) for project direction, usage validation, and documentation requirements.
2. FastAPI ecosystem for a productive async web foundation.
3. MCP community for standardizing tool interoperability.

If you continue expanding this guide, the best next step is to version it by chapter and maintain a changelog section so future readers can track protocol and implementation changes over time.

---

## Appendix A: Build This Server From Zero (Hands-On Blueprint)

This appendix is written for absolute beginners who want to recreate this project from scratch with intent, not copy-paste confusion.

### Step 0: Understand your target output

By the end, your server should do all of this:

1. Start a FastAPI app on port 10000.
2. Respond to root and health checks.
3. Accept MCP JSON-RPC at POST `/mcp`.
4. Support `initialize`, `tools/list`, and `tools/call`.
5. Expose compatibility endpoints for SSE and REST-style tool calls.
6. Return stable schemas and safe errors.
7. Pass basic route tests and formatting checks.

If any of these fail, the server is not ready for client integration.

### Step 1: Create project structure

Create the folder layout matching this repository:

1. `app/main.py`
2. `app/core/config.py`
3. `app/routes/mcp.py`
4. `app/schemas/models.py`
5. `app/services/search.py`
6. `app/services/scraper.py`
7. `tests/test_routes.py`
8. `tests/test_services.py`

Why this shape works:

1. New contributors can find code quickly.
2. Route, schema, and service responsibilities stay clear.
3. Tests can mirror the same boundaries.

### Step 2: Create the app shell in [app/main.py](app/main.py)

The first meaningful milestone is getting this to run:

1. Import FastAPI.
2. Create app object.
3. Add root endpoint and health endpoint.

At this stage, do not worry about MCP yet. Confirm simple health checks first. Beginners often skip this and end up debugging protocol issues when basic app startup was already broken.

### Step 3: Add environment-first configuration in [app/core/config.py](app/core/config.py)

Add configuration values with defaults:

1. Host and port.
2. Search and fetch timeouts.
3. MCP request timeout.
4. SSE heartbeat interval.
5. Maximum content length.

Then expose a cached `get_config()` function. This gives every module one stable configuration source.

### Step 4: Add request and response models in [app/schemas/models.py](app/schemas/models.py)

Define all payloads explicitly:

1. Search request and result models.
2. Fetch request and response models.
3. Tool listing model.
4. JSON-RPC request model.

Beginner rule: if a payload crosses the network boundary, model it.

### Step 5: Implement the search service in [app/services/search.py](app/services/search.py)

Implement small, deterministic behavior:

1. Receive query and max result count.
2. Call DuckDuckGo through a safe async wrapper.
3. Normalize result keys.
4. Return empty list on failure.

Do not return raw third-party payloads directly. Normalize once and keep your contract stable.

### Step 6: Implement the scraper service in [app/services/scraper.py](app/services/scraper.py)

Implement page fetch behavior:

1. Use `httpx.AsyncClient` with timeout.
2. Fetch page by URL.
3. Parse HTML with BeautifulSoup.
4. Strip scripts and styles.
5. Extract title and text.
6. Truncate text to safe maximum.

This creates a reusable "content extraction" primitive that many AI workflows need.

### Step 7: Implement MCP routes in [app/routes/mcp.py](app/routes/mcp.py)

Start with method router behavior for:

1. `initialize`
2. `notifications/initialized`
3. `tools/list`
4. `tools/call`

For each method, produce deterministic JSON-RPC envelopes and error codes. Keep protocol logic inside routes, and business logic inside services.

### Step 8: Register routers in [app/main.py](app/main.py)

Mount the route groups under `/mcp` and verify endpoint availability.

At this point you can run simple curl checks for:

1. Health route.
2. Initialize route.
3. Tools list route.

### Step 9: Add tests before adding more features

Write tests for the current behavior first. This creates a stable baseline and protects against accidental regressions.

### Step 10: Add docs and deployment readiness

Document:

1. Endpoint behavior.
2. Example requests.
3. Required environment variables.
4. Known troubleshooting steps.

Now your server is not just working, it is learnable and maintainable.

---

## Appendix B: End-to-End MCP Message Catalog

This catalog describes request and response examples you can use for testing and debugging.

### B.1 Initialize request

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```

Expected shape of success response:

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

### B.2 Initialized notification

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized",
  "params": {}
}
```

Expected server behavior:

1. Accept quickly.
2. Return acceptance semantics.
3. No tool work should execute here.

### B.3 Tools list request

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

Expected success response includes:

1. `name`
2. `description`
3. `inputSchema`

Note again that `inputSchema` field casing is critical for compatibility.

### B.4 Tools call request: web search

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

Expected success response includes content wrapper and non-error flag.

### B.5 Tools call request: fetch page

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

Expected payload includes title, content, and URL.

### B.6 Method-not-found response

When unsupported methods are requested, respond with JSON-RPC error envelope and stable code path.

### B.7 Timeout response

When tool execution exceeds route timeout, return deterministic error so client can decide retry behavior.

---

## Appendix C: Deployment Playbook (Render-Oriented)

This playbook gives a structured way to deploy and verify the service.

### C.1 Pre-deploy checklist

1. Formatting check passes.
2. Route tests pass.
3. Tool schema response uses `inputSchema`.
4. README and guide are aligned with code.
5. Environment variable defaults are documented.

### C.2 Environment variables to set

Recommended starting values:

1. `SEARCH_TIMEOUT=10`
2. `FETCH_TIMEOUT=10`
3. `MCP_REQUEST_TIMEOUT=25`
4. `SSE_HEARTBEAT_INTERVAL=5`

Tune gradually with real latency observations.

### C.3 Post-deploy smoke tests

Immediately after deploy, test:

1. `/health`
2. `POST /mcp` initialize
3. `POST /mcp` tools/list
4. `POST /mcp` tools/call for web_search
5. `POST /mcp` tools/call for fetch_page

If any fail, roll back or hotfix before broad usage.

### C.4 Production rollback strategy

Every deployment should have a rollback plan:

1. Keep previous known-good image/build reference.
2. Keep config diffs documented.
3. Trigger rollback if handshake fails or error rate spikes.

This protects user trust.

---

## Appendix D: CI Pipeline Design for This Project

A practical CI pipeline for this server should answer one question: "Will this break client compatibility or operational reliability?"

### D.1 Pipeline stages

1. Install dependencies.
2. Run formatter check.
3. Run linter.
4. Run route and service tests.
5. Optional: run lightweight compatibility smoke tests.

### D.2 Why formatting first

Formatting failures are cheap to detect and cheap to fix. Running Black first gives quick feedback and avoids wasted CI time.

### D.3 Contract test gate

Add a test target focused on protocol shape:

1. Initialize schema.
2. Tool list schema.
3. Tool call wrapper.

This gate protects against accidental protocol drift.

### D.4 Suggested CI failure triage order

1. Formatting failures.
2. Import or syntax errors.
3. Route test failures.
4. Service test failures.
5. Slow or flaky external-call tests.

This order reduces debugging time.

---

## Appendix E: Deep Dive Into Each Core File

This section serves as a reading map for contributors.

### E.1 [app/main.py](app/main.py)

What to inspect:

1. App metadata and initialization.
2. Middleware setup.
3. Router mounting sequence.
4. Root and health routes.

Contributor warning:

1. Avoid placing business logic here.
2. Keep this file startup-focused.

### E.2 [app/core/config.py](app/core/config.py)

What to inspect:

1. Environment variable mapping.
2. Typed defaults.
3. Cached config access.

Contributor warning:

1. Validate new config keys are documented in README.
2. Keep defaults safe and conservative.

### E.3 [app/schemas/models.py](app/schemas/models.py)

What to inspect:

1. Input constraints.
2. Output shape stability.
3. JSON-RPC model definitions.

Contributor warning:

1. Schema changes may break clients.
2. Add tests for every externally visible schema change.

### E.4 [app/routes/mcp.py](app/routes/mcp.py)

What to inspect:

1. Method router logic.
2. Error code handling.
3. Tool dispatch and timeout wrappers.
4. Compatibility endpoint behavior.

Contributor warning:

1. Avoid mixing protocol formatting with scraping logic.
2. Keep helper functions small and testable.

### E.5 [app/services/search.py](app/services/search.py)

What to inspect:

1. Thread offloading for blocking search call.
2. Timeout handling.
3. Result normalization.

Contributor warning:

1. Upstream provider behavior can change.
2. Keep resilient fallback behavior.

### E.6 [app/services/scraper.py](app/services/scraper.py)

What to inspect:

1. HTTP client configuration.
2. HTML parsing flow.
3. Content truncation behavior.

Contributor warning:

1. Avoid unbounded content extraction.
2. Keep network protections in mind.

---

## Appendix F: Performance Engineering Workbook

Use this workbook to optimize safely.

### F.1 Baseline measurement checklist

1. Measure initialize latency.
2. Measure tools/list latency.
3. Measure search latency p50/p95.
4. Measure fetch latency p50/p95.
5. Measure timeout rate.

### F.2 Load profile design

Include mixed workload:

1. 60 percent web_search.
2. 30 percent fetch_page.
3. 10 percent initialize and tools/list.

This approximates realistic MCP usage.

### F.3 Optimization candidates

1. Caching frequent search queries.
2. Reusing HTTP clients with tuned limits.
3. Tightening payload sizes.
4. Avoiding heavy logging in hot paths.

### F.4 Performance guardrails

1. Do not optimize without measurement.
2. Keep correctness tests first.
3. Re-run contract tests after optimization.

---

## Appendix G: Security Hardening Checklist

This is a practical security checklist for maintainers.

### G.1 Input security

1. Validate URL schemes.
2. Enforce query length limits.
3. Bound numeric inputs.

### G.2 Output security

1. Avoid leaking internal errors to clients.
2. Keep response content bounded.
3. Sanitize logs.

### G.3 Transport security

1. Use HTTPS in production.
2. Review CORS policy.
3. Consider origin validation if applicable.

### G.4 Dependency security

1. Keep dependency versions updated.
2. Monitor known vulnerabilities.
3. Pin critical packages where stability is required.

### G.5 Operational security

1. Protect deployment secrets.
2. Use least privilege for deployment accounts.
3. Keep incident response notes ready.

---

## Appendix H: Contributor Handbook for Future Maintainers

If this project grows, onboarding contributors efficiently becomes critical.

### H.1 Contribution workflow

1. Open issue with intent and scope.
2. Create branch.
3. Implement in small commits.
4. Add tests and docs.
5. Open PR with clear verification notes.

### H.2 PR template essentials

Every PR should include:

1. Problem statement.
2. What changed.
3. Why this design.
4. How verified.
5. Risk and rollback notes.

### H.3 Code review checklist

Reviewers should verify:

1. Protocol shape remains compatible.
2. Timeouts are enforced.
3. Error behavior remains deterministic.
4. Tests cover new logic.
5. Docs are updated.

### H.4 Documentation maintenance cadence

Update this guide whenever:

1. A new tool is added.
2. Protocol behavior changes.
3. Deployment model changes.
4. Significant incident teaches a new lesson.

---

## Appendix I: Suggested Future Roadmap for This Project

The current server is strong for a starter-to-intermediate MCP service. Here is a realistic roadmap.

### I.1 Short-term enhancements

1. Add stricter URL validation in fetch tool.
2. Add structured logging fields.
3. Add explicit contract test suite folder.

### I.2 Mid-term enhancements

1. Add optional caching layer.
2. Add richer tool result types.
3. Add improved SSE diagnostics and IDs.

### I.3 Long-term enhancements

1. Add multi-transport support.
2. Add authentication for protected deployments.
3. Add usage analytics and quota management.

Roadmaps matter because they keep a good project from becoming random patches over time.

---

## Appendix J: Final One-Stop Operational Checklist

Use this checklist before declaring the server production-ready.

### Build checklist

1. App starts locally.
2. Health endpoint works.
3. Initialize works.
4. Tool list works.
5. Tool call works for both tools.

### Quality checklist

1. Formatting check passes.
2. Lint check passes.
3. Route and service tests pass.
4. No known flaky tests.

### Protocol checklist

1. `inputSchema` field casing is correct.
2. Method-not-found response is stable.
3. Timeout behavior is deterministic.
4. Compatibility endpoint behavior is documented.

### Deployment checklist

1. Environment variables configured.
2. Smoke tests pass on deployed URL.
3. Client integration verified.
4. Rollback plan documented.

### Documentation checklist

1. README updated.
2. Developer guide updated.
3. This handbook updated.
4. Credits and ownership clear.

If every item above is true, your MCP server is not only working, it is maintainable.

---

## Appendix K: Real-World Case Studies

This appendix translates design concepts into realistic operational stories.

### Case Study 1: "Server is up, client still fails"

Observed behavior:

1. `/health` returns healthy.
2. MCP client reports failure to get tools.

Root cause pattern:

1. Protocol envelope mismatch in `tools/list`.
2. Required field names not matching client parser expectations.

Resolution strategy:

1. Test initialize and tools/list manually with JSON-RPC payloads.
2. Compare response keys to protocol expectations.
3. Add contract tests to lock shape.

Lesson:

Availability checks and compatibility checks are different dimensions.

### Case Study 2: "Random timeout only in cloud"

Observed behavior:

1. Local tests pass.
2. Cloud deployment intermittently times out.

Root cause pattern:

1. External dependency latency spike.
2. Missing or weak timeout controls.
3. Platform request limits.

Resolution strategy:

1. Add service-level and route-level timeout layers.
2. Return deterministic timeout errors.
3. Tune timeouts based on p95 latency.

Lesson:

Local success never guarantees cloud reliability.

### Case Study 3: "CI fails after tiny change"

Observed behavior:

1. Functionality works locally.
2. CI fails on formatting or linting.

Root cause pattern:

1. Style drift from automated formatter rules.

Resolution strategy:

1. Run the same formatter command locally as CI.
2. Keep formatting-only edits separate where possible.

Lesson:

Developer workflow quality is part of system reliability.

---

## Appendix L: Architecture Decision Records for MCP Projects

Architecture Decision Records (ADRs) are short documents explaining why a specific design choice was made. Beginners often skip this practice, but it is one of the fastest ways to keep a project healthy over time.

### Why ADRs matter here

This project has already made important design choices:

1. Streamable HTTP MCP as primary transport.
2. Compatibility SSE endpoint retained.
3. Service-level separation for search and scraping.
4. Timeout layering at both service and route levels.

Without ADRs, future contributors may accidentally reverse these choices without understanding their operational impact.

### Suggested ADR list for this repository

1. ADR-001: Use FastAPI for async MCP transport.
2. ADR-002: Keep route/service/schema separation.
3. ADR-003: Keep compatibility GET `/mcp` SSE stream.
4. ADR-004: Use `inputSchema` for JSON-RPC tools list responses.
5. ADR-005: Enforce multi-layer timeouts.

### ADR template

Every ADR should include:

1. Title.
2. Status (proposed, accepted, deprecated).
3. Context.
4. Decision.
5. Consequences.
6. Alternatives considered.

### Example ADR entry (condensed)

Title: Return MCP tool definitions with `inputSchema`.

Context:

1. Client reported tool discovery failure.
2. Existing payload used snake_case key.

Decision:

1. For MCP JSON-RPC tools list responses, return `inputSchema` key.

Consequences:

1. Improved interoperability with MCP clients.
2. Need dedicated contract tests to prevent regressions.

Alternatives considered:

1. Keep snake_case and handle client-specific adapters.
2. Rejected because it fragments compatibility and adds maintenance burden.

---

## Appendix M: Incident Response Guide for MCP Maintainers

A production-ready guide should include incident handling, not only coding techniques.

### Severity model

Define a simple severity scale:

1. Sev-1: Total outage or global handshake failure.
2. Sev-2: Major tool failures affecting most users.
3. Sev-3: Partial degradation or intermittent timeouts.
4. Sev-4: Minor bugs and non-blocking issues.

### First 15 minutes playbook

When an incident begins:

1. Confirm whether health endpoint is alive.
2. Run initialize and tools/list probes.
3. Check recent deploy history.
4. Classify incident severity.
5. Decide hold/rollback/hotfix path.

### Communication checklist

1. Declare incident channel.
2. Share scope, impact, and current hypothesis.
3. Share next update time.

### Technical triage sequence

1. Transport layer sanity: is endpoint reachable?
2. Protocol layer sanity: initialize and tools/list valid?
3. Tool layer sanity: can tools/call execute in bounded latency?
4. Deployment sanity: recent config or dependency drift?

### Post-incident review format

1. Timeline.
2. Root cause.
3. User impact.
4. Detection gap.
5. Prevention actions.

Beginners gain a lot by practicing postmortems even for small incidents.

---

## Appendix N: Migration Guide - From Prototype to Production MCP Server

Most MCP projects begin as prototypes. This migration guide explains how to mature responsibly.

### Phase 1: Prototype

Characteristics:

1. Few endpoints.
2. Minimal error handling.
3. Limited tests.

Upgrade goals:

1. Introduce schema validation.
2. Split service logic from route logic.
3. Add basic tests.

### Phase 2: Beta

Characteristics:

1. Multiple tools.
2. Early client integration.
3. Intermittent production use.

Upgrade goals:

1. Add timeout layering.
2. Add contract tests.
3. Add CI quality gates.
4. Add deployment runbooks.

### Phase 3: Production

Characteristics:

1. Reliable uptime expectations.
2. Multiple users or clients.
3. Need for repeatable operations.

Upgrade goals:

1. Observability dashboards.
2. Incident response policy.
3. ADR-based architecture governance.
4. Security hardening checklist enforcement.

### Phase 4: Platform

Characteristics:

1. Multiple tool domains.
2. Team contributions.
3. Versioning and compatibility pressure.

Upgrade goals:

1. Stable versioning strategy.
2. Backward compatibility tests.
3. Structured release notes and migration docs.

---

## Appendix O: MCP Design Interview Questions (Self-Assessment)

Use these questions to test your mastery.

### Protocol reasoning

1. Why can a server be reachable but still fail MCP integration?
2. Why is response key casing important for interoperability?
3. How should unknown methods be represented?

### Reliability reasoning

1. Why do you need both service and route timeouts?
2. How would you diagnose an intermittent timeout in production?
3. What metrics best detect upstream dependency instability?

### Architecture reasoning

1. Why should service code avoid transport-specific exceptions?
2. What risks appear if route and service logic are tightly coupled?
3. How would you split [app/routes/mcp.py](app/routes/mcp.py) as complexity grows?

### Operations reasoning

1. What must happen before rolling out a new tool?
2. What should a Sev-1 runbook contain?
3. How do you balance speed and safety during hotfixes?

If you can answer these with concrete examples from this repository, you are moving from beginner to practical engineer.

---

## Appendix P: Final Maintainer Notes

This handbook is intentionally large because MCP projects combine several disciplines at once:

1. API protocol design.
2. Async backend engineering.
3. External network dependency handling.
4. Reliability and operations.
5. Documentation and onboarding.

If you keep improving this guide, prioritize these principles:

1. Keep examples grounded in real repository files.
2. Prefer stable contracts over clever shortcuts.
3. Use tests as guardrails, not as decoration.
4. Keep operational knowledge close to code.

This is how a beginner-friendly project becomes an engineering-quality reference.

---

## Part III: Enterprise MCP Architecture and Governance

This part is intentionally detailed. It is written for the moment when your MCP server moves from a personal project into a team-managed service with reliability, compliance, and scaling expectations.

### 1. Single-service vs multi-service MCP design

As a beginner, a single FastAPI service is the right place to start. As usage grows, you may need to decide whether to keep all tools in one service or split them into separate services.

#### Single-service design

Pros:

1. Simple deployment.
2. Easy local development.
3. Fewer moving parts.
4. Lower operational overhead.

Cons:

1. Blast radius is larger.
2. Tool-specific scaling is harder.
3. Deploy risk affects all tools.

#### Multi-service design

Pros:

1. Independent scaling by tool domain.
2. Fault isolation.
3. Team ownership can be separated.

Cons:

1. More complex deployment and networking.
2. More CI pipelines.
3. More operational complexity.

### 2. Domain boundaries for MCP tools

For long-term sustainability, group tools by domain:

1. Discovery tools: search, trends, index lookup.
2. Content tools: fetch, parse, summarize, classify.
3. Integration tools: database, ticketing, notifications.
4. Analytics tools: metrics, reporting, benchmarking.

The current repository has a clean core around discovery and content. That is a strong foundation.

### 3. Versioning strategy for protocol and tools

Versioning is often ignored until clients break. Decide version rules early:

1. Server semantic version for implementation changes.
2. Protocol version field in initialize response.
3. Tool contract version notes in docs.

Breaking changes policy:

1. Never change input shape silently.
2. Add deprecation period.
3. Keep compatibility adapters for critical clients.

### 4. Governance model for contributions

As contributors increase, define governance:

1. Code owner rules by folder.
2. Required checks before merge.
3. Documentation update requirement.
4. Incident response escalation tree.

### 5. Service ownership model

In teams, ownership should be explicit:

1. Tool owner.
2. Transport owner.
3. CI owner.
4. Operations owner.

When ownership is unclear, bug fixes slow down and reliability suffers.

---

## Part IV: Complete MCP Tool Lifecycle

This section explains every phase in the life of a tool from idea to retirement.

### Phase 1: Idea intake

Before coding, answer:

1. What user problem does this tool solve?
2. What are the expected inputs and outputs?
3. What are failure behaviors?
4. What are latency expectations?
5. Is this tool safe to expose?

### Phase 2: Contract design

Design the input schema first:

1. Required fields.
2. Optional fields.
3. Bounds and constraints.
4. Error format.

Contract-first design reduces wasted implementation effort.

### Phase 3: Service implementation

Build the service in isolation:

1. Pure domain logic.
2. Bounded retries if needed.
3. Timeouts.
4. Safe fallbacks.

### Phase 4: Protocol integration

Wire tool into MCP routes:

1. Add tool to list.
2. Add dispatch logic.
3. Add response shaping.

### Phase 5: Testing

Add tests for:

1. Happy path.
2. Validation failures.
3. Timeout behavior.
4. Protocol contract keys.

### Phase 6: Documentation

Update:

1. README tool list.
2. Developer guide.
3. This handbook.

### Phase 7: Monitoring and iteration

After release:

1. Track latency and failure rates.
2. Observe error patterns.
3. Improve contracts and defaults.

### Phase 8: Deprecation and retirement

When removing tools:

1. Announce deprecation.
2. Provide replacement path.
3. Keep compatibility window.
4. Remove only after clients migrate.

---

## Part V: Transport Deep Dive (HTTP, SSE, and Future Transports)

### 1. Why transport choices matter

Transport determines:

1. How clients connect.
2. How messages are exchanged.
3. How failures surface.
4. How observability works.

The current project uses HTTP POST for primary MCP and SSE GET for compatibility.

### 2. Streamable HTTP behavior

Key points:

1. Client sends JSON-RPC via POST.
2. Server returns structured JSON-RPC responses.
3. Request correlation uses id field.

### 3. SSE behavior in this project

The compatibility stream:

1. Sends endpoint event first.
2. Sends connection ack.
3. Sends heartbeats on interval.

This is useful for legacy fallback and diagnostics.

### 4. Transport observability considerations

Capture metrics per transport path:

1. Request count.
2. Connection duration.
3. Error rate.
4. Disconnect reasons.

### 5. Future transport: stdio

If later adding stdio transport for local subprocess usage:

1. Keep protocol logic reusable.
2. Separate transport adapter from service logic.
3. Keep the same tool contract tests.

---

## Part VI: Advanced Schema Engineering

### 1. Schema stability principles

Good schema evolution rules:

1. Additive changes are safer than mutating existing keys.
2. Avoid changing semantic meaning of existing fields.
3. Document defaults and bounds.

### 2. Input schema defensive design

For robust tools:

1. Clamp list lengths.
2. Validate URL format.
3. Limit string sizes.
4. Normalize whitespace.

### 3. Output schema consistency

Output should remain stable across errors:

1. Always include primary keys.
2. Use explicit isError semantics where applicable.
3. Provide concise error text.

### 4. Contract test examples

Every schema key should be asserted at least once in tests.

For this repo, minimum contract tests:

1. initialize response keys.
2. tools/list key names with inputSchema.
3. tools/call content wrapper structure.

---

## Part VII: Tool Safety and Abuse Prevention

### 1. Rate limiting

Rate limits protect service quality:

1. Per-IP limits for public endpoints.
2. Per-session limits for client identities.
3. Burst and sustained limits.

### 2. Payload size controls

Limit request and response sizes:

1. Max request body size.
2. Max fetched content length.
3. Max number of search results.

### 3. SSRF-aware URL policy

For fetch tools, enforce rules:

1. Block private network ranges where possible.
2. Block file and local schemes.
3. Limit redirects and timeout aggressively.

### 4. User-agent strategy

A consistent user-agent can reduce random upstream behavior and helps troubleshooting.

### 5. Denial-of-wallet protection

Even "free" tools can consume money through compute and traffic. Enforce:

1. Strict timeouts.
2. Request budgets.
3. Alerting on spikes.

---

## Part VIII: Reliability Patterns in Detail

### 1. Timeout layering model

Use layered timeouts:

1. Outbound call timeout.
2. Service operation timeout.
3. Route-level overall timeout.

Each layer catches different failure modes.

### 2. Retry policy design

Retry only for transient errors and only when safe.

For read-only operations like search/fetch:

1. One retry may be acceptable.
2. Add jitter.
3. Respect overall timeout budget.

### 3. Backpressure and queue control

When request volume spikes:

1. Reject quickly rather than timing out all requests.
2. Keep service responsive for healthy traffic.

### 4. Graceful degradation

When dependencies fail:

1. Return empty search list rather than crash.
2. Return fetch error content with stable structure.
3. Keep non-dependent endpoints healthy.

### 5. Dependency health classification

Classify dependencies by criticality:

1. Critical: required for handshake and route operation.
2. Important: required for specific tools.
3. Optional: enhancements.

Use this to prioritize incident response.

---

## Part IX: Deep Observability Implementation Guide

### 1. Log structure template

Preferred log fields:

1. timestamp
2. level
3. request_id
4. method
5. tool_name
6. duration_ms
7. outcome
8. error_class

### 2. Request ID propagation

Add a request ID at route entry and include it in all downstream logs. This turns scattered lines into traceable narratives.

### 3. Metrics naming convention

Examples:

1. mcp_request_total
2. mcp_request_duration_ms
3. mcp_tool_call_total
4. mcp_tool_timeout_total
5. mcp_tool_error_total

### 4. Dashboard starter pack

Create dashboards for:

1. Overall request volume.
2. Error rates by endpoint.
3. p95 latency by tool.
4. Timeout trends.
5. Deployment correlation with error spikes.

### 5. Alerting policy

Start with simple alerts:

1. Error rate exceeds threshold.
2. Timeout rate spikes.
3. Health endpoint failures.

Escalate severity based on duration and breadth.

---

## Part X: Comprehensive Testing Program

### 1. Unit testing patterns

For service code:

1. Test output normalization.
2. Test timeout branch.
3. Test exception branch.

### 2. Route testing patterns

For MCP routes:

1. Test method routing.
2. Test unknown method errors.
3. Test schema key casing.
4. Test argument validation behavior.

### 3. Integration testing patterns

Use mocked services to avoid flaky external dependencies while still validating route-service wiring.

### 4. Contract testing patterns

Create contract-focused tests that fail when envelope keys or nested shapes change.

### 5. Chaos testing ideas

Simulate instability:

1. Random timeout injection.
2. Random upstream 5xx responses.
3. Slow response tails.

Measure whether service remains predictable.

### 6. Testing anti-patterns to avoid

1. Asserting exact external content text.
2. Relying on real network for all tests.
3. Ignoring timeout branches.
4. Treating warning signs as acceptable noise.

---

## Part XI: CI/CD at Scale

### 1. Pipeline stages with clear outcomes

Suggested stages:

1. Static quality stage.
2. Unit and route tests.
3. Contract test stage.
4. Packaging stage.
5. Deployment stage.
6. Post-deploy verification stage.

### 2. Merge policy

Require:

1. Green checks.
2. Review from code owner.
3. Updated docs for behavior changes.

### 3. Deployment gates

Block rollout when:

1. Tool discovery checks fail.
2. Initialize response invalid.
3. Critical tests flaky or red.

### 4. Post-deploy auto-checks

Automate:

1. health check.
2. initialize call.
3. tools/list call.
4. one tool call.

If any fail, notify and rollback.

---

## Part XII: Performance Engineering Deep Lab

### 1. Baseline profiling exercise

Measure before changing anything:

1. cold start time.
2. warm request latency.
3. tool call latency distribution.

### 2. Optimization experiment design

Run one change at a time:

1. Adjust timeout values.
2. Adjust max results.
3. Adjust content length cap.
4. Add cache and compare hit rate.

### 3. Throughput tuning

Tune with caution:

1. worker count.
2. connection pool settings.
3. request queue policy.

### 4. Memory management

Watch for:

1. oversized content blobs.
2. large logging payloads.
3. unbounded in-memory caches.

### 5. Performance budgets

Define target budgets per route and monitor drift over time.

---

## Part XIII: Multi-Environment Strategy

### 1. Environment taxonomy

Use clear environments:

1. local
2. dev
3. staging
4. production

### 2. Config differences by environment

Document what may vary:

1. timeout values.
2. logging verbosity.
3. security policy strictness.

### 3. Promotion flow

Recommended:

1. feature branch -> dev.
2. release candidate -> staging.
3. validated release -> production.

### 4. Drift prevention

Use the same baseline checks across environments to avoid surprises in production.

---

## Part XIV: Documentation as an Engineering System

### 1. Documentation layers

Maintain three layers:

1. Quick usage docs (README).
2. Developer docs (DEVELOPER_GUIDE).
3. Deep handbook (this file).

### 2. Documentation quality checklist

Every major change should update docs with:

1. what changed.
2. why it changed.
3. how to test it.
4. migration notes.

### 3. Keeping docs trustworthy

Outdated docs are worse than no docs. Add doc review in code review checklist.

### 4. Example-driven style

Use real payloads and file references from the repository. This improves learning speed for beginners.

---

## Part XV: Security and Compliance Expansion

### 1. Data classification

Classify data handled by tools:

1. public web content.
2. potentially sensitive query text.
3. operational metadata.

### 2. Retention policy

Define what to retain and for how long:

1. logs retention window.
2. debug payload retention policy.
3. redaction rules.

### 3. Compliance readiness basics

Even small teams should prepare:

1. documented access policy.
2. change audit trail.
3. incident recordkeeping.

### 4. Responsible disclosure

Define how security issues can be reported and triaged.

---

## Part XVI: Team Enablement and Onboarding Curriculum

### Week 1 onboarding plan

1. Read README and this handbook introduction.
2. Run project locally.
3. Execute tests.
4. Trace one request across route -> service -> response.

### Week 2 onboarding plan

1. Add a small tool or validation improvement.
2. Add tests.
3. Update docs.
4. Ship through CI.

### Week 3 onboarding plan

1. Handle a small incident simulation.
2. Write a mini postmortem.
3. Propose one reliability improvement.

### Mentor checklist

Mentors should verify that new contributors can:

1. explain initialize and tools/list flows.
2. reason about timeout layering.
3. write a schema-safe change.

---

## Part XVII: Advanced MCP Patterns for Future Evolution

### Pattern 1: Tool metadata enrichment

Add metadata that helps clients choose tools intelligently, such as latency class or expected cost.

### Pattern 2: Policy-aware execution

Introduce policy checks before tool execution:

1. rate policy
2. domain allow/block policy
3. request budget policy

### Pattern 3: Preflight validation layer

Add a preflight stage that validates tool arguments and policy before service calls begin.

### Pattern 4: Structured content variants

Return both text and structured JSON content variants for richer client behavior.

### Pattern 5: Tool orchestration workflows

Build orchestrated server-side workflows for multi-step retrieval tasks, while preserving deterministic timeout envelopes.

---

## Part XVIII: Full Beginner-to-Expert Practice Labs

### Lab 1: Add a trivial hello tool

Goal:

1. Understand full tool lifecycle with minimum complexity.

Steps:

1. Add tool schema.
2. Add route dispatch.
3. Add contract test.
4. Add docs entry.

### Lab 2: Add URL validation to fetch tool

Goal:

1. Practice security hardening.

Steps:

1. Add validation helper.
2. Reject invalid schemes.
3. Add tests for blocked URLs.

### Lab 3: Add structured logging fields

Goal:

1. Improve observability.

Steps:

1. Add request_id.
2. log method/tool/duration.
3. verify logs in local run.

### Lab 4: Add timeout stress tests

Goal:

1. Ensure bounded behavior under slow dependencies.

Steps:

1. Mock slow service.
2. assert timeout response.
3. confirm error envelope stability.

### Lab 5: Deployment validation drill

Goal:

1. Build operational confidence.

Steps:

1. Deploy branch.
2. run smoke checks.
3. validate opencode mcp list.
4. document results.

---

## Part XIX: Interview-Style Deep Questions and Model Answers

### Question 1

Why do you need both service-level and route-level timeouts?

Model answer:

1. Service-level timeouts bound individual dependency calls.
2. Route-level timeout bounds the end-to-end request budget.
3. Both are needed to avoid hangs and maintain predictable latency envelopes.

### Question 2

What can break MCP compatibility even when the endpoint is live?

Model answer:

1. Incorrect JSON-RPC envelope shape.
2. Wrong key casing in tool schemas.
3. Missing or malformed initialize response fields.

### Question 3

How do you scale this server safely?

Model answer:

1. Measure first.
2. Tune timeouts and payload bounds.
3. add caching where justified.
4. keep contract tests as release gates.

### Question 4

How do you onboard new contributors quickly?

Model answer:

1. provide layered docs.
2. give small labs.
3. enforce test and documentation updates in each PR.

---

## Part XX: Closing Reference Checklist for One-Stop MCP Mastery

Use this final checklist to ensure you can design and operate an MCP server end to end.

### Architecture mastery

1. Can explain route/service/schema boundaries.
2. Can justify timeout layering.
3. Can reason about transport compatibility.

### Protocol mastery

1. Can implement initialize flow from memory.
2. Can design tool list and tool call envelopes.
3. Can diagnose method-not-found and schema mismatch issues.

### Reliability mastery

1. Can design runbooks.
2. Can triage cloud-only timeouts.
3. Can implement graceful degradation.

### Quality mastery

1. Can write contract tests.
2. Can keep CI green.
3. Can document behavioral changes clearly.

### Operational mastery

1. Can run deployment smoke tests.
2. Can rollback safely.
3. Can write incident summaries and prevention actions.

If you can complete every item above with examples from this repository, you now have a strong practical foundation for building and maintaining real MCP servers.

---

## Part XXI: Protocol Compatibility Matrix and Validation Framework

When MCP servers are used by multiple clients, compatibility management becomes a first-class engineering problem. This part gives a practical framework to keep your server compatible across clients and releases.

### 1. Build a compatibility matrix

Create a table that maps each client against each critical protocol behavior:

1. Initialize handshake.
2. Notification handling.
3. Tool discovery (`tools/list`).
4. Tool call envelopes.
5. Error code parsing.
6. Transport fallback behavior.

Maintain this table in your repository docs so compatibility assumptions are explicit.

### 2. Define required and optional protocol behaviors

Not all behaviors are equally critical. For your project:

1. Required: initialize, tools/list, tools/call.
2. Required: stable JSON-RPC envelopes.
3. Optional: legacy compatibility stream.

This distinction helps prioritize bug fixes and release gates.

### 3. Add compatibility test suites

Beyond unit tests, add compatibility tests that assert behavior from a client viewpoint:

1. Request shape in.
2. Envelope shape out.
3. Stable key casing and field names.

### 4. Release gating by compatibility class

Before merging, classify changes:

1. Non-breaking internal change.
2. Potentially breaking schema change.
3. Breaking transport behavior.

Require stricter review and staged rollout for higher-risk classes.

### 5. Deprecation policy for protocol behavior

If behavior must change:

1. Document old and new behavior.
2. Keep fallback path for a window.
3. Provide migration examples.

---

## Part XXII: Full Request Lifecycle Trace (Micro-Level)

This part traces requests at micro-level detail so beginners understand exactly where latency and failures occur.

### 1. Lifecycle for initialize

1. HTTP POST accepted by FastAPI.
2. Request body parsed into JSONRPCRequest model.
3. Method router matches `initialize`.
4. Capabilities object generated.
5. JSON-RPC result envelope returned.

Potential failure points:

1. Invalid JSON payload.
2. Missing required method.
3. Serialization errors.

### 2. Lifecycle for tools/list

1. JSON-RPC request validated.
2. Method router matches `tools/list`.
3. Tool definitions assembled.
4. Keys mapped to MCP-compatible form.
5. Result envelope returned.

Potential failure points:

1. Incorrect field naming.
2. Non-serializable schema values.

### 3. Lifecycle for tools/call web_search

1. Request and params parsed.
2. Tool name validated.
3. Dispatch helper called.
4. Search service invoked with timeout.
5. Search provider call occurs.
6. Results normalized.
7. Content envelope built and returned.

Potential failure points:

1. Missing tool arguments.
2. Upstream timeout.
3. Provider response shape drift.

### 4. Lifecycle for tools/call fetch_page

1. Request parsed and validated.
2. URL extracted.
3. Scraper service invoked with timeout.
4. Outbound HTTP call performed.
5. HTML parsed.
6. Content extracted and bounded.
7. Result wrapped and returned.

Potential failure points:

1. Invalid URL.
2. Timeout.
3. HTTP status failures.
4. Parsing errors.

---

## Part XXIII: Architecture Patterns for Growing MCP Toolsets

As tool count grows, architecture pressure increases. This chapter gives concrete evolution patterns.

### Pattern A: Registry-based tool dispatch

Instead of long if/elif chains, use a registry map:

1. key: tool name.
2. value: async callable + schema metadata.

Advantages:

1. Cleaner extension.
2. Less merge conflict risk.
3. Easier dynamic validation.

### Pattern B: Capability modules

Group tools by module:

1. `capabilities/search`
2. `capabilities/content`
3. `capabilities/integrations`

Route layer imports capability registry, not tool implementations directly.

### Pattern C: Policy middleware layer

Insert a pre-dispatch policy layer:

1. Authentication policy.
2. Rate policy.
3. URL safety policy.
4. Quota policy.

### Pattern D: Output adapters

Some clients may prefer richer structures. Use adapters:

1. canonical internal result shape.
2. transport-specific output rendering.

### Pattern E: Structured error domain

Define internal error classes:

1. validation errors.
2. dependency errors.
3. timeout errors.
4. policy errors.

Then map these consistently to JSON-RPC error envelopes.

---

## Part XXIV: Security Engineering Implementation Playbook

This chapter transforms security goals into concrete engineering actions.

### 1. Threat model walkthrough

For this server, assume:

1. Untrusted clients can send malformed tool calls.
2. Untrusted URLs can target internal resources.
3. Attackers can send repeated heavy requests.
4. Dependencies can be compromised or unstable.

### 2. Security controls matrix

Map threats to controls:

1. Malformed payloads -> schema validation + size limits.
2. SSRF attempts -> URL validation + private IP denylist.
3. abuse traffic -> rate limits + request budgets.
4. data leakage -> log redaction + bounded error messages.

### 3. URL validation checklist

For `fetch_page` style tools:

1. allow only http/https.
2. reject localhost and internal hostnames where possible.
3. reject private IP targets.
4. cap redirect count.
5. cap response body size.

### 4. Safe logging template

Log useful context without sensitive payload exposure:

1. include route, tool, duration, result class.
2. avoid full page content in logs.
3. avoid query text if privacy constraints require masking.

### 5. Security testing plan

Add tests for:

1. blocked URL schemes.
2. oversized body handling.
3. malformed JSON-RPC payloads.
4. policy rejection behavior.

---

## Part XXV: Advanced Reliability Engineering (SLOs, SLIs, Error Budgets)

### 1. Define service level indicators (SLIs)

Useful SLIs for MCP server:

1. availability of initialize endpoint.
2. successful tools/list response rate.
3. successful tools/call rate.
4. latency percentiles per tool.

### 2. Define service level objectives (SLOs)

Example starter SLOs:

1. initialize success >= 99.9 percent.
2. tools/list success >= 99.5 percent.
3. tools/call success >= 98 percent.

### 3. Error budget operations

If error budget burns too fast:

1. slow feature rollout.
2. prioritize reliability fixes.
3. increase test coverage for failing class.

### 4. Failure containment strategy

Contain failures by:

1. per-tool isolation.
2. deterministic timeout boundaries.
3. graceful fallback responses.

---

## Part XXVI: Operational Readiness Handbook

### 1. Day-0 readiness

Before first production use:

1. docs complete.
2. tests complete.
3. deployment verified.
4. on-call owner identified.

### 2. Day-1 operations

In early production:

1. monitor logs closely.
2. validate client behavior daily.
3. tune timeout defaults with observed data.

### 3. Day-2 operations

In steady state:

1. weekly reliability review.
2. monthly dependency updates.
3. quarterly architecture review.

### 4. On-call quick commands and checks

Document exact checks:

1. health endpoint check.
2. initialize check.
3. tools/list check.
4. tool smoke call.

Keep this in one runbook for speed during incidents.

---

## Part XXVII: Data Handling, Privacy, and Governance

### 1. Data minimization principle

Collect and store only what is needed:

1. required operational logs.
2. bounded debug data.
3. no unnecessary payload retention.

### 2. Privacy-aware query handling

Queries may include sensitive intent. Consider:

1. hashing or masking in logs.
2. reduced retention windows.
3. role-limited log access.

### 3. Content handling policy

Fetched web content can be large and noisy. Store minimally and process with boundaries.

### 4. Governance controls

1. review policy for new tools.
2. review policy for new data fields.
3. change audit for protocol behavior.

---

## Part XXVIII: Dependency Strategy and Supply Chain Safety

### 1. Pinning and update policy

Balance stability and security:

1. pin production-critical versions.
2. schedule regular dependency update windows.
3. test compatibility before promoting.

### 2. Monitoring dependency health

Track:

1. deprecation warnings.
2. vulnerability advisories.
3. major API changes.

### 3. Fallback plans for upstream provider changes

For search provider drift:

1. normalize outputs in one place.
2. keep provider-specific parsing isolated.
3. prepare alternate provider adapter path.

---

## Part XXIX: Enterprise-Grade CI/CD Blueprint

### 1. Multi-stage pipeline blueprint

Stage 1: style and static checks.

Stage 2: fast tests.

Stage 3: contract tests.

Stage 4: package and artifact integrity checks.

Stage 5: deploy to staging + smoke tests.

Stage 6: controlled production rollout.

### 2. Progressive delivery pattern

Deploy safely with phased rollout:

1. small traffic slice.
2. observe metrics.
3. expand if healthy.

### 3. Automatic rollback trigger design

Rollback when:

1. initialize failures spike.
2. tools/list compatibility checks fail.
3. timeout rate exceeds threshold.

### 4. Release notes discipline

Every release should include:

1. behavior changes.
2. compatibility notes.
3. migration guidance.
4. rollback notes.

---

## Part XXX: Scaling and Cost Optimization

### 1. Cost drivers in MCP servers

1. outbound HTTP volume.
2. compute time for parsing.
3. high-cardinality logging.
4. repeated identical requests without cache.

### 2. Cost controls

1. strict timeouts.
2. response size limits.
3. bounded retries.
4. caching with TTL.

### 3. Throughput scaling strategy

1. optimize hot paths first.
2. scale horizontally when needed.
3. isolate heavy tools if required.

### 4. Cost-observability loop

Track cost against:

1. request volume.
2. tool mix.
3. error and timeout rates.

Use this to guide optimization priorities.

---

## Part XXXI: Full Course-Style Practice Curriculum

### Module 1: MCP fundamentals

Deliverables:

1. explanation of initialize flow.
2. manual tools/list request and response analysis.

### Module 2: Build and run

Deliverables:

1. local server run.
2. health and root checks.

### Module 3: Protocol implementation

Deliverables:

1. add one new lightweight tool.
2. add contract tests.

### Module 4: Reliability lab

Deliverables:

1. timeout simulations.
2. fallback behavior validation.

### Module 5: Operations lab

Deliverables:

1. deployment smoke checklist.
2. incident response mini-drill.

### Module 6: Security lab

Deliverables:

1. URL policy tests.
2. abuse-prevention baseline.

### Module 7: Performance lab

Deliverables:

1. baseline latency report.
2. optimization experiment results.

### Module 8: Documentation and teaching

Deliverables:

1. add one handbook subsection.
2. explain one architecture decision with ADR.

---

## Part XXXII: Extended FAQ (Deep Answers)

### Q1: Why not return raw provider responses for speed?

Raw responses are unstable and provider-specific. Normalization gives contract stability and protects clients from upstream shape drift.

### Q2: Why keep both MCP and legacy endpoints?

Compatibility and debugging. Legacy paths can ease migration and isolate protocol vs service issues.

### Q3: Why are strict schemas important for beginners?

Schemas reduce ambiguity and debugging time. They force explicit thinking about contracts.

### Q4: How do I know a timeout value is correct?

Measure real latency distributions and set timeouts that balance responsiveness with legitimate slow responses. Revisit periodically.

### Q5: What is the fastest path to production confidence?

Reliable tests + strict contracts + smoke checks + rollback readiness.

### Q6: What is the biggest mistake in MCP projects?

Treating protocol details as optional. Most integration failures come from subtle schema or envelope mismatches.

### Q7: How can I mentor others using this repository?

Use layered progression:

1. read architecture.
2. trace one request.
3. ship one small feature.
4. write tests and docs.

### Q8: Should I optimize before adding observability?

No. Observe first, optimize second.

### Q9: How do I keep documentation from becoming stale?

Make docs updates a required part of every behavior-changing PR.

### Q10: What does mature MCP engineering look like?

Predictable contracts, resilient operations, disciplined releases, and clear documentation.

---

## Part XXXIII: Final Mega Checklist for 100% Readiness

### Protocol readiness

1. initialize correct.
2. tools/list correct key casing.
3. tools/call consistent envelope.
4. unknown methods handled.

### Reliability readiness

1. multi-layer timeouts active.
2. graceful fallback responses.
3. health probes reliable.

### Security readiness

1. URL validation policy.
2. payload size controls.
3. safe logging practices.

### Testing readiness

1. route tests green.
2. service tests green.
3. contract tests green.

### CI readiness

1. formatting check green.
2. lint check green.
3. test stages green.

### Deployment readiness

1. env vars set.
2. smoke tests pass.
3. rollback path documented.

### Documentation readiness

1. README accurate.
2. developer guide accurate.
3. handbook updated.

### Team readiness

1. ownership clear.
2. runbook available.
3. escalation path defined.

If all items are true, your MCP server is not just functional; it is operationally mature.

---

## Final Extended Credits

This handbook exists to make MCP server development approachable for beginners while still useful for serious engineering workflows.

Primary credit:

1. Himanshu (`himanshu231204`) for project direction, requirements, and practical validation.

Project context credit:

1. FastAPI for production-friendly async web framework capabilities.
2. Pydantic for robust schema validation.
3. MCP ecosystem for interoperability standards.

This guide can continue evolving with additional chapters for multi-tenant auth, distributed tracing implementation code, and full reference architecture diagrams.