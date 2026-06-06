# src/interpark_mcp/mcp/tools/domestic.py
from datetime import date
from interpark_mcp.core.interfaces import FlightSearcher
from interpark_mcp.core.models import Flight
from interpark_mcp.dependencies.requester import get_requester


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


async def search_domestic_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    adult: int = 1,
    child: int = 0,
    infant: int = 0,
    requester: FlightSearcher = get_requester(),
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
    )
    return [_flight_to_dict(f) for f in flights]
