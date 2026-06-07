# src/aeromcp/infra/parser.py
import re
from datetime import datetime, timedelta
from aeromcp.core.models import (
    Baggage, Schedule, CardCashback, Benefit, PassengerFare, Fare, Flight,
)


def parse_iso_duration(duration: str) -> timedelta:
    hours = int(m.group(1)) if (m := re.search(r"(\d+)H", duration)) else 0
    minutes = int(m.group(1)) if (m := re.search(r"(\d+)M", duration)) else 0
    return timedelta(hours=hours, minutes=minutes)


def _parse_cashback(raw: dict) -> CardCashback:
    return CardCashback(
        card_name=raw["cardName"],
        rate=raw["rate"],
        amount=raw["amount"],
        discounted_price=raw["discountedPrice"],
        cashback_date=raw["cashbackDate"],
        method=raw["method"],
    )


def _parse_benefit(raw: dict) -> Benefit:
    cashback_raw = raw.get("cardCashback")
    return Benefit(
        discounted_price=raw["discountedPrice"],
        card_cashback=_parse_cashback(cashback_raw) if cashback_raw else None,
    )


def _parse_passenger_fare(raw: dict) -> PassengerFare:
    return PassengerFare(
        type=raw["type"],
        count=raw["count"],
        air_price=raw["airPrice"],
        other_tax=raw["otherTax"],
        fuel_charge=raw["fuelCharge"],
        ticketing_fee=raw["ticketingFee"],
        discount=raw["discount"],
        total=raw["total"],
    )


def _parse_fare(raw: dict) -> Fare:
    return Fare(
        total_price=raw["totalPrice"],
        passenger_fares=[_parse_passenger_fare(p) for p in raw["passengerFares"]],
        tags=raw.get("tags", []),
        benefits=[_parse_benefit(b) for b in raw.get("benefits", [])],
    )


def _parse_schedule(raw: dict) -> Schedule:
    return Schedule(
        departure=raw["departure"],
        arrival=raw["arrival"],
        departure_at=datetime.fromisoformat(raw["departureAt"]),
        arrival_at=datetime.fromisoformat(raw["arrivalAt"]),
        marketing_carrier=raw["marketingCarrier"],
        flight_number=raw["flightNumber"],
        flight_time=parse_iso_duration(raw["flightTime"]),
        free_baggage=Baggage(
            volume=raw["freeBaggage"]["volume"],
            unit=raw["freeBaggage"]["unit"],
        ),
    )


def parse_flight(raw: dict) -> Flight:
    return Flight(
        id=raw["id"],
        key=raw["key"],
        fares=[_parse_fare(f) for f in raw["fares"]],
        seat_availability=raw["seatAvailability"],
        cabin=raw["cabin"],
        discount_type=raw["discountType"],
        schedule=_parse_schedule(raw["schedule"]),
    )
