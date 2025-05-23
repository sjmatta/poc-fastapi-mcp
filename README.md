# Lorem Ipsum MCP + FastAPI

[![Tests](https://github.com/sjmatta/poc-fastapi-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/sjmatta/poc-fastapi-mcp/actions/workflows/test.yml)

Minimal FastAPI app serving both REST APIs and MCP functionality.

## Setup

```bash
# Install dependencies
uv sync

# For local testing with OpenAI (optional)
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Run Server

```bash
uv run uvicorn main:app --reload
```

## Test REST APIs

```bash
# In another terminal
uv run python test_both.py
```

## MCP Integration with LM Studio

### Important: MCP vs REST
The test shows REST endpoints work. For true MCP integration:

1. **MCP Server runs at**: `http://localhost:8000/mcp/mcp` (SSE endpoint)
2. **Configure LM Studio**: Copy `mcp_config.json` settings to LM Studio
3. **In LM Studio chat**: The model will have access to `generate_lorem_ipsum` tool

### Setup MCP in LM Studio:
1. Open LM Studio → Developer → MCP Servers
2. Add the configuration from `mcp_config.json`
3. Restart LM Studio
4. In chat, ask: "Use the generate_lorem_ipsum tool to create 2 paragraphs"

## Endpoints

### REST API
- `GET /health` - Health check
- `GET /lorem/{count}` - Get lorem paragraphs

### MCP Protocol
- `/mcp/mcp` - SSE endpoint for MCP communication
- Tool: `generate_lorem_ipsum(paragraph_count=1)`

## Architecture
This demonstrates a single FastAPI app serving:
- Traditional REST APIs (synchronous HTTP)
- MCP tools (SSE-based protocol for LLM integration)

## Testing GitHub Actions Locally

Install `act` to test GitHub Actions locally:
```bash
brew install act  # macOS
# or see https://github.com/nektos/act for other platforms

# List workflows
make act-list

# Run tests locally (requires Docker)
make act-test
```