#!/usr/bin/env python3
"""
MCP Server for Code Analysis Tools using Anthropic's fastmcp Framework
"""

import importlib
import os
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
import uvicorn

# Create the MCP server instance
mcp = FastMCP("Code Analysis Tools")

# Import and register resources
from src.resources.status import register_status_resource
register_status_resource(mcp)

# Import and register tools
from src.tools import register_all_tools
register_all_tools(mcp)

# Create a Starlette application with the SSE endpoint
app = Starlette(routes=[
    # Mount the SSE app at the root
    Mount("/", app=mcp.sse_app()),
])

def main():
    """Run the MCP server."""
    print("Starting Code Analysis MCP server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
