# tests/mcp/test_roundtrip.py
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock
import pytest
from aeromcp.core.models import Flight, Fare, PassengerFare, Schedule, Baggage
from aeromcp.mcp.tools.roundtrip import find_cheapest_roundtrip


def make_flight(flight_id: str, carrier: str, price: int, dep: str, arr: str, dep_at: datetime) -> Flight:
    return Flight(
        id=flight_id,
        key=f"{carrier}_key",
        fares=[Fare(
            total_price=price,
            passenger_fares=[PassengerFare(
                type="ADULT", count=1, air_price=price - 10000, other_tax=4000,
                fuel_charge=5000, ticketing_fee=1000, discount=0, total=price,
            )],
            tags=[],
            benefits=[],
        )],
        seat_availability=9,
        cabin="ECONOMY",
        discount_type="DISCOUNT",
        schedule=Schedule(
            departure=dep, arrival=arr,
            departure_at=dep_at,
            arrival_at=dep_at + timedelta(hours=1, minutes=5),
            marketing_carrier=carrier,
            flight_number="1234",
            flight_time=timedelta(hours=1, minutes=5),
            free_baggage=Baggage(volume=15, unit="WEIGHT_KG"),
        ),
    )


@pytest.mark.asyncio
async def test_find_cheapest_roundtrip_combinations():
    mock = AsyncMock()
    outbound_flights = [
        make_flight("OUT1", "BX", 80000, "GMP", "CJU", datetime(2026, 7, 1, 9, 0)),
        make_flight("OUT2", "TW", 90000, "GMP", "CJU", datetime(2026, 7, 1, 14, 0)),
    ]
    inbound_flights = [
        make_flight("IN1", "BX", 75000, "CJU", "GMP", datetime(2026, 7, 5, 10, 0)),
        make_flight("IN2", "TW", 85000, "CJU", "GMP", datetime(2026, 7, 5, 18, 0)),
    ]
    mock.search_domestic.side_effect = [outbound_flights, inbound_flights]

    result = await find_cheapest_roundtrip(
        origin="GMP", destination="CJU",
        departure_date="2026-07-01", return_date="2026-07-05",
        requester=mock,
    )

    combos = result["combinations"]
    assert len(combos) == 4
    assert combos[0]["total_price"] == 155000  # OUT1 + IN1
    assert combos[0]["outbound"]["id"] == "OUT1"
    assert combos[0]["inbound"]["id"] == "IN1"
    assert combos[-1]["total_price"] == 175000  # OUT2 + IN2
    assert len(result["outbound_flights"]) == 2
    assert len(result["inbound_flights"]) == 2


@pytest.mark.asyncio
async def test_find_cheapest_roundtrip_top_n():
    mock = AsyncMock()
    outbound_flights = [make_flight(f"OUT{i}", "BX", 80000 + i * 1000, "GMP", "CJU", datetime(2026, 7, 1, 9+i, 0)) for i in range(3)]
    inbound_flights = [make_flight(f"IN{i}", "BX", 75000 + i * 1000, "CJU", "GMP", datetime(2026, 7, 5, 10+i, 0)) for i in range(3)]
    mock.search_domestic.side_effect = [outbound_flights, inbound_flights]

    result = await find_cheapest_roundtrip(
        origin="GMP", destination="CJU",
        departure_date="2026-07-01", return_date="2026-07-05",
        top_n=3,
        requester=mock,
    )

    assert len(result["combinations"]) == 3
    prices = [c["total_price"] for c in result["combinations"]]
    assert prices == sorted(prices)
