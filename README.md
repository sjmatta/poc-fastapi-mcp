# Lorem Ipsum MCP + FastAPI

[![Tests](https://github.com/sjmatta/poc-fastapi-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/sjmatta/poc-fastapi-mcp/actions/workflows/test.yml)

Minimal FastAPI app serving both REST APIs and MCP functionality from a single application.

## Quick Start

```bash
# Install dependencies
uv sync

# Run server
make run

# Run tests
make test-quick
```

## Features

- **REST API**: Traditional HTTP endpoints
  - `GET /health` - Health check
  - `GET /lorem/{count}` - Generate lorem ipsum paragraphs

- **MCP Protocol**: LLM tool integration via SSE
  - Tool: `generate_lorem_ipsum(paragraph_count: int)`
  - Endpoint: `/mcp/mcp`

## Development

```bash
# All tests (including LLM integration)
make test

# Test with server running
make test-server

# Test GitHub Actions locally
make act-test
```

## Configuration

- Copy `.env.example` to `.env` for API keys
- See `mcp_config.json` for LM Studio MCP setup

## Architecture

Single FastAPI application serving:
- Traditional REST APIs (synchronous HTTP)
- MCP tools (SSE-based protocol for LLM integration)

Built with [uv](https://github.com/astral-sh/uv) for fast Python dependency management.