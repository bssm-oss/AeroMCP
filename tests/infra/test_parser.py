# tests/infra/test_parser.py
from datetime import datetime, timedelta
from aeromcp.infra.parser import parse_flight, parse_iso_duration

RAW_FLIGHT = {
    "id": "TW0933L",
    "key": "TW_uuid_0",
    "fares": [
        {
            "totalPrice": 68900,
            "passengerFares": [
                {
                    "type": "ADULT", "count": 1,
                    "airPrice": 30900, "otherTax": 4000,
                    "fuelCharge": 33000, "ticketingFee": 1000,
                    "discount": 0, "total": 68900,
                }
            ],
            "tags": [],
            "benefits": [
                {
                    "discountedPrice": 67890,
                    "cardCashback": {
                        "discountedPrice": 67890, "amount": 1010,
                        "method": "RATE", "cardName": "삼성카드",
                        "rate": 1.5, "cashbackDate": "2026-09-30",
                        "type": "CARD_CASHBACK",
                    },
                }
            ],
        }
    ],
    "seatAvailability": 9,
    "cabin": "ECONOMY",
    "discountType": "DISCOUNT",
    "schedule": {
        "arrival": "PUS", "arrivalAt": "2026-06-08T12:55:00",
        "departure": "GMP", "departureAt": "2026-06-08T11:50:00",
        "marketingCarrier": "TW",
        "freeBaggage": {"volume": 15, "unit": "WEIGHT_KG"},
        "flightTime": "PT1H5M",
        "flightNumber": "0933",
    },
}


def test_parse_iso_duration_hours_minutes():
    assert parse_iso_duration("PT1H5M") == timedelta(hours=1, minutes=5)


def test_parse_iso_duration_minutes_only():
    assert parse_iso_duration("PT20M") == timedelta(minutes=20)


def test_parse_iso_duration_hours_only():
    assert parse_iso_duration("PT2H") == timedelta(hours=2)


def test_parse_flight_id():
    flight = parse_flight(RAW_FLIGHT)
    assert flight.id == "TW0933L"


def test_parse_flight_schedule():
    flight = parse_flight(RAW_FLIGHT)
    assert flight.schedule.departure == "GMP"
    assert flight.schedule.arrival == "PUS"
    assert flight.schedule.departure_at == datetime(2026, 6, 8, 11, 50)
    assert flight.schedule.flight_time == timedelta(hours=1, minutes=5)
    assert flight.schedule.free_baggage.volume == 15


def test_parse_flight_fare():
    flight = parse_flight(RAW_FLIGHT)
    fare = flight.fares[0]
    assert fare.total_price == 68900
    assert fare.passenger_fares[0].air_price == 30900


def test_parse_flight_cashback():
    flight = parse_flight(RAW_FLIGHT)
    cashback = flight.fares[0].benefits[0].card_cashback
    assert cashback is not None
    assert cashback.rate == 1.5
    assert cashback.card_name == "삼성카드"
