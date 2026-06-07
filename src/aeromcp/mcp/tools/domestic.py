# src/aeromcp/mcp/tools/domestic.py
from collections import defaultdict
from datetime import date
from aeromcp.core.interfaces import FlightSearcher
from aeromcp.core.models import Flight
from aeromcp.dependencies.requester import get_requester


def _flight_to_dict(flight: Flight) -> dict:
    fare = flight.fares[0] if flight.fares else None
    cashback = None
    if fare and fare.benefits and fare.benefits[0].card_cashback:
        cb = fare.benefits[0].card_cashback
        cashback = {
            "card_name": cb.card_name,
            "rate": cb.rate,
            "amount": cb.amount,
            "discounted_price": cb.discounted_price,
        }
    return {
        "id": flight.id,
        "total_price": fare.total_price if fare else None,
        "departure": flight.schedule.departure,
        "arrival": flight.schedule.arrival,
        "departure_at": flight.schedule.departure_at.isoformat(),
        "arrival_at": flight.schedule.arrival_at.isoformat(),
        "carrier": flight.schedule.marketing_carrier,
        "flight_number": flight.schedule.flight_number,
        "flight_time_minutes": int(flight.schedule.flight_time.total_seconds() // 60),
        "free_baggage_kg": flight.schedule.free_baggage.volume,
        "seat_availability": flight.seat_availability,
        "cabin": flight.cabin,
        "discount_type": flight.discount_type,
        "cashback": cashback,
    }


_CARRIER_NAMES: dict[str, str] = {
    "KE": "대한항공",
    "OZ": "아시아나항공",
    "7C": "제주항공",
    "LJ": "진에어",
    "BX": "에어부산",
    "TW": "티웨이항공",
    "ZE": "이스타항공",
    "RS": "에어서울",
    "4V": "플라이강원",
    "YP": "에어프레미아",
}

_AIRPORT_NAMES: dict[str, str] = {
    "SEL": "서울 (도시코드, GMP+ICN)",
    "GMP": "서울/김포",
    "ICN": "서울/인천",
    "CJU": "제주",
    "PUS": "부산/김해",
    "KWJ": "광주",
    "MWX": "무안",
    "KUV": "군산",
    "TAE": "대구",
    "HIN": "진주/사천",
    "RSU": "여수",
    "USN": "울산",
    "WJU": "원주",
    "CJJ": "청주",
    "KPO": "포항",
    "YNY": "양양",
}


def _build_metadata(flights: list[dict]) -> dict:
    carriers = sorted({f["carrier"] for f in flights})
    airports = sorted({f["departure"] for f in flights} | {f["arrival"] for f in flights})
    return {
        "carriers": {c: _CARRIER_NAMES.get(c, c) for c in carriers},
        "airports": {a: _AIRPORT_NAMES.get(a, a) for a in airports},
    }


def _time_slot(hour: int) -> str:
    if hour < 6:
        return "dawn"
    if hour < 12:
        return "morning"
    if hour < 18:
        return "afternoon"
    return "evening"


def _analyze(flights: list[dict]) -> dict:
    by_slot: dict[str, list[int]] = defaultdict(list)
    by_airline: dict[str, list[int]] = defaultdict(list)

    for f in flights:
        price = f["total_price"]
        if price is None:
            continue
        hour = int(f["departure_at"][11:13])
        by_slot[_time_slot(hour)].append(price)
        by_airline[f["carrier"]].append(price)

    def summarize(prices: list[int]) -> dict:
        return {
            "count": len(prices),
            "avg_price": round(sum(prices) / len(prices)),
            "min_price": min(prices),
            "max_price": max(prices),
        }

    slot_order = ["dawn", "morning", "afternoon", "evening"]
    return {
        "by_time_slot": {
            slot: summarize(by_slot[slot])
            for slot in slot_order
            if slot in by_slot
        },
        "by_airline": {
            carrier: summarize(prices)
            for carrier, prices in sorted(by_airline.items())
        },
    }


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
    requester: FlightSearcher = get_requester(),
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
    dep = date.fromisoformat(departure_date)
    ret = date.fromisoformat(return_date) if return_date else None

    flights = await requester.search_domestic(
        origin=origin,
        destination=destination,
        departure_date=dep,
        return_date=ret,
        adult=adult,
        child=child,
        infant=infant,
        cabin=cabin,
        airlines=airlines,
    )
    flight_dicts = [_flight_to_dict(f) for f in flights]
    return {
        "result": flight_dicts,
        "analysis": _analyze(flight_dicts),
        "metadata": _build_metadata(flight_dicts),
    }
