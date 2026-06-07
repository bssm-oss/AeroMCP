# src/interpark_mcp/mcp/server.py
from fastmcp import FastMCP
from interpark_mcp.mcp.banner import BANNER
from interpark_mcp.mcp.tools.domestic import search_domestic_flights

mcp = FastMCP("interpark-mcp")
mcp.tool(exclude_args=["requester"])(search_domestic_flights)


def main() -> None:
    print(BANNER, flush=True)
    mcp.run(show_banner=False)
