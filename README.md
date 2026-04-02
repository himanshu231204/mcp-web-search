# MCP Web Search Server

A fast, async [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides web search and webpage content extraction capabilities via FastAPI.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![CI Tests](https://github.com/yourusername/mcp-web-search/actions/workflows/test.yml/badge.svg)](https://github.com/yourusername/mcp-web-search/actions)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

MCP Web Search Server is a lightweight, production-ready MCP tool server that enables AI models and applications to:

- **Search the web** using DuckDuckGo with customizable result counts
- **Fetch and parse webpage content** with automatic title extraction and text cleanup
- **Integrate seamlessly** with MCP clients via REST API endpoints

Built with **async/await patterns** for high performance and non-blocking I/O.

## Features

✨ **Core Capabilities**
- Web search via DuckDuckGo (1-20 results per request)
- Webpage fetching with HTML parsing and content extraction
- Automatic page title detection
- Content length limiting for safe response sizes
- Request input validation using Pydantic

🔌 **OpenCode SSE Compatibility**
- Server-Sent Events (SSE) streaming for MCP root endpoint
- SSE-based tool execution via `/mcp/run`
- Fully compatible with OpenCode MCP client
- Event format: `event: {type}` + `data: {json}`

🚀 **Production Ready**
- Async FastAPI framework for high concurrency
- Health check endpoints (`/health`, `/`)
- CORS enabled for cross-origin requests
- Comprehensive error handling and logging
- Environment-based configuration
- Docker support

📋 **Developer Friendly**
- Type hints on all functions
- Clear separation of concerns (routes, services, schemas)
- Extensive documentation and code comments
- Developer guide included

## Quick Start

### Prerequisites

- **Python 3.11 or later**
- **pip** or your preferred Python package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mcp-web-search.git
   cd mcp-web-search
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Create a `.env` file** for configuration
   ```bash
   cp .env.example .env
   ```

### Running the Server

**Development mode** (with auto-reload):
```bash
python -m app.main
```

**Production mode**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

The server will start on `http://localhost:10000`

### Health Check

```bash
curl http://localhost:10000/health
```

Returns:
```json
{"status": "healthy"}
```

## API Endpoints

### MCP Root (SSE)

```http
GET /mcp
Accept: text/event-stream
```

Returns a Server-Sent Events (SSE) stream for OpenCode MCP compatibility.

**Response:**
```
event: ready
data: {"status": "ok", "message": "MCP Web Search Server ready"}
```

### List Available Tools

```http
GET /mcp/tools
```

Returns a list of available MCP tools with their descriptions and input schemas.

### Execute Tool (SSE)

```http
POST /mcp/run
Content-Type: application/json
Accept: text/event-stream

{
  "tool": "web_search",
  "input": {
    "query": "python async programming",
    "num_results": 5
  }
}
```

**Parameters:**
- `tool` (string, required): Tool name (`web_search` or `fetch_page`)
- `input` (object, required): Tool input parameters

**Response (SSE stream):**
```
event: start
data: {"tool": "web_search", "input": {...}}

event: data
data: {"status": "searching", "query": "python async programming"}

event: data
data: {"status": "complete", "results": [...]}

event: end
data: {"status": "done", "tool": "web_search"}
```

### Web Search (Legacy REST)

```http
POST /mcp/tools/web_search
Content-Type: application/json

{
  "query": "python async programming",
  "num_results": 5
}
```

**Parameters:**
- `query` (string, required): Search query (1-500 chars)
- `num_results` (integer, optional): Number of results to return (1-20, default: 5)

**Response:**
```json
{
  "results": [
    {
      "title": "Async IO in Python",
      "url": "https://example.com/async-python",
      "snippet": "Learn about async/await in Python..."
    },
    ...
  ]
}
```

### Fetch Webpage (Legacy REST)

```http
POST /mcp/tools/fetch_page
Content-Type: application/json

{
  "url": "https://example.com/article"
}
```

```http
POST /mcp/tools/fetch_page
Content-Type: application/json

{
  "url": "https://example.com/article"
}
```

**Parameters:**
- `url` (string, required): URL to fetch

**Response:**
```json
{
  "title": "Article Title",
  "content": "Full page content as plain text...",
  "url": "https://example.com/article"
}
```

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    FastAPI App                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────┐ │
│  │  Routes/MCP    │  │   Services     │  │  Schemas   │ │
│  │  Endpoints     │──│  (Search,      │──│  (Models)  │ │
│  │                │  │   Scraper)     │  │            │ │
│  └────────────────┘  └────────────────┘  └────────────┘ │
│         │                     │                            │
│         ├─────────────────────┴──────────────────┐        │
│         ▼                                        ▼        │
│   ┌──────────────────────────────────────────────────┐   │
│   │    Core Configuration (config.py)               │   │
│   │  Settings, Environment Variables, Defaults      │   │
│   └──────────────────────────────────────────────────┘   │
│                                                           │
│   External Dependencies:                                 │
│   • DuckDuckGo Search API                               │
│   • httpx (async HTTP client)                           │
│   • BeautifulSoup (HTML parsing)                        │
└──────────────────────────────────────────────────────────┘
```

## Project Structure

```
mcp-web-search/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # Configuration & settings management
│   ├── routes/
│   │   ├── __init__.py
│   │   └── mcp.py             # MCP endpoint handlers
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── models.py          # Pydantic request/response models
│   └── services/
│       ├── __init__.py
│       ├── search.py          # DuckDuckGo search implementation
│       └── scraper.py         # Webpage fetching & parsing
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker image configuration
├── render.yaml                 # Render deployment config
├── CODE_OF_CONDUCT.md         # Contributor Code of Conduct
├── README.md                  # This file
└── LICENSE                    # MIT License

# Local development files (not committed to git)
├── AGENTS.md                  # Agent coding guidelines
└── DEVELOPER_GUIDE.md         # Internal architecture details
```

## Configuration

Settings are managed through the `Config` class in `app/core/config.py` and can be customized via environment variables.

### Environment Variables

Create a `.env` file in the project root:

```env
# App Settings
APP_NAME=MCP Web Search Server
VERSION=1.0.0
HOST=0.0.0.0
PORT=10000

# Search Configuration
DEFAULT_NUM_RESULTS=5
MAX_NUM_RESULTS=20

# Scraper Configuration
FETCH_TIMEOUT=10
SEARCH_TIMEOUT=10
MAX_CONTENT_LENGTH=5000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=20
```

### Configuration Details

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | MCP Web Search Server | Application name |
| `VERSION` | 1.0.0 | Application version |
| `HOST` | 0.0.0.0 | Server host address |
| `PORT` | 10000 | Server port |
| `DEFAULT_NUM_RESULTS` | 5 | Default search results |
| `MAX_NUM_RESULTS` | 20 | Maximum search results per request |
| `FETCH_TIMEOUT` | 10 | Webpage fetch timeout (seconds) |
| `SEARCH_TIMEOUT` | 10 | Search request timeout (seconds) |
| `MAX_CONTENT_LENGTH` | 5000 | Max characters in fetched content |
| `RATE_LIMIT_PER_MINUTE` | 20 | Rate limit per IP address |

## Development

### Development Server

Run the development server with auto-reload:

```bash
python -m app.main
```

### Code Quality Tools

**Linting** (using ruff):
```bash
ruff check app/
```

**Auto-fix issues**:
```bash
ruff check --fix app/
```

**Code formatting** (using black):
```bash
black app/
```

**Type checking** (using mypy):
```bash
mypy app/
```

### Testing

For test development, install test dependencies:

```bash
pip install pytest pytest-asyncio httpx
```

Run tests:
```bash
# All tests
pytest

# Specific test file
pytest tests/test_services.py

# Specific test function with verbose output
pytest tests/test_services.py::test_search_service -v

# Run with coverage report
pytest --cov=app --cov-report=html
```

### Automated Testing (CI/CD)

This project uses **GitHub Actions** for continuous integration:

**Test Workflow** (`test.yml`):
- Runs on every push to `main` and `develop` branches
- Runs on all pull requests
- Tests Python 3.11 and 3.12
- Performs linting, formatting checks, type checking, and pytest suite
- Uploads coverage reports to Codecov

**Deploy Workflow** (`deploy.yml`):
- Runs on every push to `main` branch
- Automatically deploys to Render using API keys
- Requires GitHub Secrets configuration (see [.github/workflows/README.md](.github/workflows/README.md))

Check workflow status in the **Actions** tab of your GitHub repository.

### Code Style Guidelines

- **Line length**: Maximum 100 characters
- **Indentation**: 4 spaces
- **Type hints**: Required on all functions
- **Docstrings**: Google-style for public methods
- **Imports**: Standard library → third-party → local, grouped with blank lines

See [AGENTS.md](AGENTS.md) for additional coding standards.

## Deployment

### Docker

Build and run using Docker:

```bash
# Build the image
docker build -t mcp-web-search .

# Run the container
docker run -p 10000:10000 mcp-web-search
```

### Render

This project includes `render.yaml` for deployment on [Render](https://render.com/):

1. Push your repository to GitHub
2. Connect your GitHub repository to Render
3. Create a new Web Service
4. Select the repository and set the build command to `pip install -r requirements.txt`

**Automated Deployment:**

Enable automatic deployment via GitHub Actions:

1. Set up GitHub Secrets for Render API access (see [.github/workflows/README.md](.github/workflows/README.md))
2. Push to the `main` branch
3. The `deploy.yml` workflow will automatically trigger a Render deployment
4. Monitor deployment status in GitHub **Actions** tab and Render dashboard

See [GitHub Workflows Setup](https://github.com/yourusername/mcp-web-search/blob/main/.github/workflows/README.md) for detailed configuration.

### Production Checklist

- ✅ Set environment variables in your hosting platform
- ✅ Use a production ASGI server (e.g., Gunicorn)
- ✅ Configure appropriate timeouts for your use case
- ✅ Monitor logs and error rates
- ✅ Set up rate limiting based on your needs
- ✅ Enable HTTPS/TLS for secure communication

## Dependencies

| Package | Purpose |
|---------|---------|
| [FastAPI](https://fastapi.tiangolo.com/) | Web framework |
| [httpx](https://www.python-httpx.org/) | Async HTTP client |
| [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing |
| [duckduckgo-search](https://github.com/deedy5/duckduckgo_search) | DuckDuckGo API client |
| [uvicorn](https://www.uvicorn.org/) | ASGI server |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable management |
| [pydantic](https://docs.pydantic.dev/) | Data validation |

## Performance Characteristics

- **Search latency**: ~500-2000ms depending on query complexity
- **Page fetch latency**: ~1-5s depending on page size and complexity
- **Concurrent request limit**: Handled by Uvicorn worker configuration
- **Memory usage**: ~100-200MB base, scales with concurrent requests

## Error Handling

The server gracefully handles various error scenarios:

- **Search errors**: Returns empty results list with error logging
- **Network timeouts**: Returns appropriate HTTP error codes
- **Invalid input**: Returns HTTP 422 with validation error details
- **Server errors**: Returns HTTP 500 with logged error context

## Troubleshooting

### Port Already in Use

```bash
# Change the port
python -m app.main --port 10001
```

### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### DuckDuckGo Search Not Working

- Check your internet connection
- DuckDuckGo may rate-limit excessive requests; implement backoff in client
- Check `SEARCH_TIMEOUT` setting for slow connections

### Large Webpage Timeouts

- Reduce `FETCH_TIMEOUT` to fail faster
- Adjust `MAX_CONTENT_LENGTH` to process smaller portions
- Consider using client-side timeouts as well

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure code follows the style guidelines in [AGENTS.md](AGENTS.md) and passes linting checks.

## Documentation

- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** – Architecture details, module descriptions, and extension patterns
- **[AGENTS.md](AGENTS.md)** – Code style, naming conventions, error handling, and development guidelines

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [DuckDuckGo](https://duckduckgo.com/)
- HTML parsing with [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Model Context Protocol](https://modelcontextprotocol.io/) for standardized AI tool integration


---

**Last Updated**: 2026-04-03  
**Status**: Production Ready ✅
