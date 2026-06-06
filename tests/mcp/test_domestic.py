# tests/mcp/test_domestic.py
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock
import pytest
from interpark_mcp.core.models import Flight, Fare, PassengerFare, Schedule, Baggage
from interpark_mcp.mcp.tools.domestic import search_domestic_flights


def make_fake_flight() -> Flight:
    return Flight(
        id="TW0933L",
        key="TW_uuid_0",
        fares=[Fare(
            total_price=68900,
            passenger_fares=[PassengerFare(
                type="ADULT", count=1, air_price=30900, other_tax=4000,
                fuel_charge=33000, ticketing_fee=1000, discount=0, total=68900,
            )],
            tags=[],
            benefits=[],
        )],
        seat_availability=9,
        cabin="ECONOMY",
        discount_type="DISCOUNT",
        schedule=Schedule(
            departure="GMP", arrival="CJU",
            departure_at=datetime(2026, 6, 20, 11, 50),
            arrival_at=datetime(2026, 6, 20, 12, 55),
            marketing_carrier="TW",
            flight_number="0933",
            flight_time=timedelta(hours=1, minutes=5),
            free_baggage=Baggage(volume=15, unit="WEIGHT_KG"),
        ),
    )


@pytest.mark.asyncio
async def test_search_domestic_flights_returns_formatted_list():
    mock_searcher = AsyncMock()
    mock_searcher.search_domestic.return_value = [make_fake_flight()]

    result = await search_domestic_flights(
        origin="GMP",
        destination="CJU",
        departure_date="2026-06-20",
        requester=mock_searcher,
    )

    assert len(result) == 1
    assert result[0]["id"] == "TW0933L"
    assert result[0]["total_price"] == 68900
    assert result[0]["departure"] == "GMP"
    assert result[0]["departure_at"] == "2026-06-20T11:50:00"
    mock_searcher.search_domestic.assert_called_once_with(
        origin="GMP", destination="CJU",
        departure_date=date(2026, 6, 20),
        return_date=None, adult=1, child=0, infant=0,
    )


@pytest.mark.asyncio
async def test_search_domestic_flights_empty():
    mock_searcher = AsyncMock()
    mock_searcher.search_domestic.return_value = []

    result = await search_domestic_flights(
        origin="GMP", destination="CJU",
        departure_date="2026-06-20",
        requester=mock_searcher,
    )
    assert result == []
