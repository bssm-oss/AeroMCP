# tests/core/test_models.py
from datetime import datetime, timedelta, date
from interpark_mcp.core.models import (
    Baggage, Schedule, CardCashback, Benefit, PassengerFare, Fare, Flight
)

def test_baggage_fields():
    b = Baggage(volume=15, unit="WEIGHT_KG")
    assert b.volume == 15
    assert b.unit == "WEIGHT_KG"

def test_schedule_fields():
    s = Schedule(
        departure="GMP",
        arrival="PUS",
        departure_at=datetime(2026, 6, 20, 11, 50),
        arrival_at=datetime(2026, 6, 20, 12, 55),
        marketing_carrier="TW",
        flight_number="0933",
        flight_time=timedelta(hours=1, minutes=5),
        free_baggage=Baggage(volume=15, unit="WEIGHT_KG"),
    )
    assert s.departure == "GMP"
    assert s.flight_time == timedelta(hours=1, minutes=5)

def test_flight_total_price():
    fare = Fare(
        total_price=68900,
        passenger_fares=[
            PassengerFare(
                type="ADULT", count=1,
                air_price=30900, other_tax=4000,
                fuel_charge=33000, ticketing_fee=1000,
                discount=0, total=68900,
            )
        ],
        tags=[],
        benefits=[],
    )
    flight = Flight(
        id="TW0933L",
        key="TW_uuid_0",
        fares=[fare],
        seat_availability=9,
        cabin="ECONOMY",
        discount_type="DISCOUNT",
        schedule=Schedule(
            departure="GMP", arrival="PUS",
            departure_at=datetime(2026, 6, 20, 11, 50),
            arrival_at=datetime(2026, 6, 20, 12, 55),
            marketing_carrier="TW", flight_number="0933",
            flight_time=timedelta(hours=1, minutes=5),
            free_baggage=Baggage(volume=15, unit="WEIGHT_KG"),
        ),
    )
    assert flight.fares[0].total_price == 68900
    assert flight.id == "TW0933L"
