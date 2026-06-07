# src/aeromcp/mcp/tools/roundtrip.py
import asyncio
from datetime import date
from aeromcp.core.interfaces import FlightSearcher
from aeromcp.dependencies.requester import get_requester
from aeromcp.mcp.tools.domestic import _flight_to_dict


async def find_cheapest_roundtrip(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str,
    adult: int = 1,
    child: int = 0,
    infant: int = 0,
    cabin: str | None = None,
    airlines: list[str] | None = None,
    top_n: int = 5,
    requester: FlightSearcher = get_requester(),
) -> dict:
    """왕복 최저가 조합 탐색.

    Args:
        origin: 출발 IATA 코드 (예: GMP, SEL)
        destination: 도착 IATA 코드 (예: CJU, PUS)
        departure_date: 출발일 YYYY-MM-DD
        return_date: 귀국일 YYYY-MM-DD
        adult: 성인 수 (기본 1)
        child: 소아 수 (기본 0)
        infant: 유아 수 (기본 0)
        cabin: 좌석 등급 필터 - ECONOMY 또는 BUSINESS (기본 None=전체)
        airlines: 항공사 필터 - IATA 코드 목록 예: ["BX", "TW"] (기본 None=전체)
        top_n: 반환할 최저가 조합 수 (기본 5)
    """
    dep = date.fromisoformat(departure_date)
    ret = date.fromisoformat(return_date)

    common = dict(adult=adult, child=child, infant=infant, cabin=cabin, airlines=airlines)

    outbound_raw, inbound_raw = await asyncio.gather(
        requester.search_domestic(origin=origin, destination=destination, departure_date=dep, **common),
        requester.search_domestic(origin=destination, destination=origin, departure_date=ret, **common),
    )

    outbound = [_flight_to_dict(f) for f in outbound_raw]
    inbound = [_flight_to_dict(f) for f in inbound_raw]

    combinations = sorted(
        [
            {
                "total_price": (o["total_price"] or 0) + (i["total_price"] or 0),
                "outbound": o,
                "inbound": i,
            }
            for o in outbound
            for i in inbound
            if o["total_price"] is not None and i["total_price"] is not None
        ],
        key=lambda x: x["total_price"],
    )

    return {
        "combinations": combinations[:top_n],
        "outbound_flights": outbound,
        "inbound_flights": inbound,
    }
