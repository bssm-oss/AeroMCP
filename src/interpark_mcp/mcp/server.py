# src/interpark_mcp/mcp/server.py
from fastmcp import FastMCP
from interpark_mcp.mcp.banner import BANNER
from interpark_mcp.mcp.tools.domestic import search_domestic_flights as _search_impl

mcp = FastMCP("interpark-mcp")


@mcp.tool()
async def search_domestic_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    adult: int = 1,
    child: int = 0,
    infant: int = 0,
) -> list[dict]:
    """국내선 항공권 검색.

    Args:
        origin: 출발 IATA 코드 (예: GMP, SEL)
        destination: 도착 IATA 코드 (예: CJU, PUS)
        departure_date: 출발일 YYYY-MM-DD
        return_date: 귀국일 YYYY-MM-DD (편도면 None)
        adult: 성인 수 (기본 1)
        child: 소아 수 (기본 0)
        infant: 유아 수 (기본 0)
    """
    return await _search_impl(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        adult=adult,
        child=child,
        infant=infant,
    )


def main() -> None:
    print(BANNER, flush=True)
    mcp.run(show_banner=False)
