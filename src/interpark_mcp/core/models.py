# src/interpark_mcp/core/models.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class Baggage:
    volume: int
    unit: str  # "WEIGHT_KG"


@dataclass
class Schedule:
    departure: str      # IATA 공항/도시 코드
    arrival: str
    departure_at: datetime
    arrival_at: datetime
    marketing_carrier: str  # 항공사 IATA 코드
    flight_number: str
    flight_time: timedelta
    free_baggage: Baggage


@dataclass
class CardCashback:
    card_name: str
    rate: float
    amount: int
    discounted_price: int
    cashback_date: str   # "YYYY-MM-DD"
    method: str          # "RATE"


@dataclass
class Benefit:
    discounted_price: int
    card_cashback: CardCashback | None = None


@dataclass
class PassengerFare:
    type: str       # "ADULT" | "CHILD" | "INFANT"
    count: int
    air_price: int
    other_tax: int
    fuel_charge: int
    ticketing_fee: int
    discount: int
    total: int


@dataclass
class Fare:
    total_price: int
    passenger_fares: list[PassengerFare]
    tags: list[str]
    benefits: list[Benefit] = field(default_factory=list)


@dataclass
class Flight:
    id: str               # e.g. "TW0933L"
    key: str              # e.g. "TW_uuid_0"
    fares: list[Fare]
    seat_availability: int
    cabin: str            # "ECONOMY" | "BUSINESS"
    discount_type: str    # "DISCOUNT" | "NORMAL" | "SPECIAL_DISCOUNT"
    schedule: Schedule
