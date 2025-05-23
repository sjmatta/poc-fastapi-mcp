from fastapi import FastAPI
from fastmcp import FastMCP
import lorem
import uvicorn

# Create MCP server
mcp = FastMCP("Lorem Ipsum MCP")

# MCP tool
@mcp.tool()
async def generate_lorem_ipsum(paragraph_count: int = 1) -> str:
    """Generate lorem ipsum text with specified number of paragraphs."""
    if paragraph_count == 1:
        return lorem.paragraph()
    return lorem.text()

# Create MCP app and FastAPI with shared lifespan
mcp_app = mcp.http_app(path='/mcp')
app = FastAPI(lifespan=mcp_app.lifespan)
app.mount("/mcp", mcp_app)

# REST API endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/lorem/{count}")
async def get_lorem_paragraphs(count: int):
    paragraphs = [lorem.paragraph() for _ in range(count)]
    return {"paragraphs": paragraphs}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)