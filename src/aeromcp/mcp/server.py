# src/aeromcp/mcp/server.py
from fastmcp import FastMCP
from aeromcp.mcp.banner import BANNER
from aeromcp.mcp.tools.domestic import search_domestic_flights as _search_impl

mcp = FastMCP("aeromcp")


@mcp.tool()
async def search_domestic_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    adult: int = 1,
    child: int = 0,
    infant: int = 0,
    cabin: str | None = None,
    airlines: list[str] | None = None,
) -> dict:
    """국내선 항공권 검색 및 분석.

    Args:
        origin: 출발 IATA 코드 (예: GMP, SEL)
        destination: 도착 IATA 코드 (예: CJU, PUS)
        departure_date: 출발일 YYYY-MM-DD
        return_date: 귀국일 YYYY-MM-DD (편도면 None)
        adult: 성인 수 (기본 1)
        child: 소아 수 (기본 0)
        infant: 유아 수 (기본 0)
        cabin: 좌석 등급 필터 - ECONOMY 또는 BUSINESS (기본 None=전체)
        airlines: 항공사 필터 - IATA 코드 목록 예: ["BX", "TW"] (기본 None=전체)
    """
    return await _search_impl(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        adult=adult,
        child=child,
        infant=infant,
        cabin=cabin,
        airlines=airlines,
    )


def main() -> None:
    print(BANNER, flush=True)
    mcp.run(show_banner=False)
