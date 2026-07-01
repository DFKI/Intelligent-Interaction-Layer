#!/usr/bin/env python3
"""
mcp/server.py — CE services MCP Server

Exposes all 5 CE tools (including the service registry) via the
Model Context Protocol so that any MCP-compatible client
(Claude Desktop, Continue, etc.) can call them.

Run as module (recommended):
    python -m mcp.server

Or directly:
    python mcp/server.py

Or register in mcp_config.json:
    {
        "servers": {
            "ce-services": {
                "command": "python",
                "args": ["-m", "mcp.server"]
            }
        }
    }
"""

import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from . import ALL_TOOLS_SCHEMA, execute_tool

# ---------------------------------------------------------------------------
# MCP application
# ---------------------------------------------------------------------------

app = Server("ce-services")


# ---------------------------------------------------------------------------
# Tool registry — build Tool objects from ALL_TOOLS_SCHEMA
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Advertise all CE tools to the MCP client."""
    tools = []
    for schema in ALL_TOOLS_SCHEMA:
        fn = schema["function"]
        tools.append(
            Tool(
                name=fn["name"],
                description=fn["description"],
                inputSchema=fn["parameters"],
            )
        )
    return tools


# ---------------------------------------------------------------------------
# Tool call handler
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route an MCP tool call to the matching CE function and return JSON."""
    result = execute_tool(name, arguments)
    return [
        TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False),
        )
    ]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(stdio_server(app))
