# src/interpark_mcp/mcp/server.py
from fastmcp import FastMCP
from interpark_mcp.mcp.tools.domestic import search_domestic_flights

mcp = FastMCP("interpark-mcp")
mcp.tool()(search_domestic_flights)


def main() -> None:
    mcp.run()
