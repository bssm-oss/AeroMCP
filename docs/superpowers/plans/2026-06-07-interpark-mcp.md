# interpark-mcp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 인터파크 국내선 항공권 검색 기능을 제공하는 fastmcp MCP 서버 구현.

**Architecture:** `core`(모델/추상)를 중심으로 `infra`가 구현체, `dependencies`가 DI 팩토리, `mcp`가 도구 정의. `infra`는 인터파크 3단계 API 플로우(SSR buildId 추출 → 검색 세션 생성 → 결과 조회)를 캡슐화.

**Tech Stack:** Python 3.11+, fastmcp, httpx, pytest, pytest-asyncio

---

## 파일 구조

```
interpark-mcp/
├── pyproject.toml
├── main.py
├── src/interpark_mcp/
│   ├── __init__.py
│   ├── common/
│   │   ├── __init__.py
│   │   └── config.py           # 상수, base URL, 브라우저 헤더
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py           # Flight, Fare, Schedule 등 dataclass
│   │   └── interfaces.py       # FlightSearcher ABC
│   ├── infra/
│   │   ├── __init__.py
│   │   ├── build_id.py         # Next.js buildId 추출/캐시
│   │   ├── parser.py           # API 응답 dict → dataclass 변환
│   │   └── requester.py        # InterparkRequester (FlightSearcher 구현)
│   ├── dependencies/
│   │   ├── __init__.py
│   │   └── requester.py        # get_requester() 팩토리
│   └── mcp/
│       ├── __init__.py
│       └── tools/
│           ├── __init__.py
│           └── domestic.py     # @mcp.tool search_domestic_flights
└── tests/
    ├── conftest.py
    ├── core/
    │   └── test_models.py
    ├── infra/
    │   ├── test_build_id.py
    │   ├── test_parser.py
    │   └── test_requester.py
    └── mcp/
        └── test_domestic.py
```

---

## Task 0: 프로젝트 셋업

**Files:**
- Create: `pyproject.toml`
- Create: `src/interpark_mcp/__init__.py`
- Create: `src/interpark_mcp/common/__init__.py`
- Create: `src/interpark_mcp/core/__init__.py`
- Create: `src/interpark_mcp/infra/__init__.py`
- Create: `src/interpark_mcp/dependencies/__init__.py`
- Create: `src/interpark_mcp/mcp/__init__.py`
- Create: `src/interpark_mcp/mcp/tools/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: pyproject.toml 작성**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "interpark-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.0.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "respx>=0.21.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.hatch.build.targets.wheel]
packages = ["src/interpark_mcp"]
```

- [ ] **Step 2: 패키지 디렉토리 및 빈 `__init__.py` 생성**

```bash
mkdir -p src/interpark_mcp/{common,core,infra,dependencies,mcp/tools}
mkdir -p tests/{core,infra,mcp}
touch src/interpark_mcp/__init__.py
touch src/interpark_mcp/common/__init__.py
touch src/interpark_mcp/core/__init__.py
touch src/interpark_mcp/infra/__init__.py
touch src/interpark_mcp/dependencies/__init__.py
touch src/interpark_mcp/mcp/__init__.py
touch src/interpark_mcp/mcp/tools/__init__.py
touch tests/__init__.py tests/core/__init__.py tests/infra/__init__.py tests/mcp/__init__.py
touch tests/conftest.py
```

- [ ] **Step 3: 의존성 설치**

```bash
pip install -e ".[dev]"
```

Expected: 설치 완료, 오류 없음.

- [ ] **Step 4: pytest 동작 확인**

```bash
pytest --collect-only
```

Expected: `no tests ran` (아직 테스트 없음), 오류 없음.

---

## Task 1: Core 모델

**Files:**
- Create: `src/interpark_mcp/core/models.py`
- Create: `tests/core/test_models.py`

인터파크 API 응답 구조를 그대로 반영한 dataclass. 외부 의존성 없음.

- [ ] **Step 1: 테스트 작성**

```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/core/test_models.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'interpark_mcp.core.models'`

- [ ] **Step 3: 모델 구현**

```python
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/core/test_models.py -v
```

Expected: 3 passed.

- [ ] **Step 5: 커밋**

```bash
git add src/interpark_mcp/core/models.py tests/core/test_models.py
git commit -m "feat(core): add domain models"
```

---

## Task 2: Core 인터페이스

**Files:**
- Create: `src/interpark_mcp/core/interfaces.py`
- Create: `tests/core/test_interfaces.py`

- [ ] **Step 1: 테스트 작성**

```python
# tests/core/test_interfaces.py
from datetime import date
from unittest.mock import AsyncMock
from interpark_mcp.core.interfaces import FlightSearcher
from interpark_mcp.core.models import Flight


def test_flight_searcher_is_abstract():
    import inspect
    assert inspect.isabstract(FlightSearcher)


async def test_concrete_subclass_works():
    class MockSearcher(FlightSearcher):
        async def search_domestic(self, origin, destination, departure_date,
                                   return_date=None, adult=1, child=0, infant=0):
            return []

    searcher = MockSearcher()
    result = await searcher.search_domestic("GMP", "CJU", date(2026, 6, 20))
    assert result == []
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/core/test_interfaces.py -v
```

Expected: FAIL

- [ ] **Step 3: 인터페이스 구현**

```python
# src/interpark_mcp/core/interfaces.py
from abc import ABC, abstractmethod
from datetime import date
from interpark_mcp.core.models import Flight


class FlightSearcher(ABC):
    @abstractmethod
    async def search_domestic(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date | None = None,
        adult: int = 1,
        child: int = 0,
        infant: int = 0,
    ) -> list[Flight]:
        """국내선 항공편 검색. origin/destination은 IATA 코드."""
        ...
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/core/ -v
```

Expected: all passed.

- [ ] **Step 5: 커밋**

```bash
git add src/interpark_mcp/core/interfaces.py tests/core/test_interfaces.py
git commit -m "feat(core): add FlightSearcher abstract interface"
```

---

## Task 3: Common Config

**Files:**
- Create: `src/interpark_mcp/common/config.py`

- [ ] **Step 1: config 작성**

```python
# src/interpark_mcp/common/config.py

INTERPARK_BASE_URL = "https://travel.interpark.com"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": f"{INTERPARK_BASE_URL}/air",
}

# 국내 도시코드 (공항코드가 아닌 것). c: prefix 사용.
DOMESTIC_CITY_CODES = {"SEL"}

# 검색 상태 폴링 설정
POLL_MAX_ATTEMPTS = 15
POLL_INTERVAL_SECONDS = 1.0
```

- [ ] **Step 2: import 확인**

```bash
python -c "from interpark_mcp.common.config import BROWSER_HEADERS; print(BROWSER_HEADERS['User-Agent'][:20])"
```

Expected: `Mozilla/5.0 (Macintosh`

- [ ] **Step 3: 커밋**

```bash
git add src/interpark_mcp/common/config.py
git commit -m "feat(common): add config constants"
```

---

## Task 4: BuildId 추출

**Files:**
- Create: `src/interpark_mcp/infra/build_id.py`
- Create: `tests/infra/test_build_id.py`

인터파크 HTML에서 Next.js buildId를 파싱 및 캐싱.

- [ ] **Step 1: 테스트 작성**

```python
# tests/infra/test_build_id.py
import pytest
import respx
import httpx
from interpark_mcp.infra.build_id import extract_build_id, get_build_id, _cache


FAKE_HTML = """
<html><body>
<script id="__NEXT_DATA__" type="application/json">
{"buildId":"XalSUGjxvqXwyKRn4Rjgj","page":"/"}
</script>
</body></html>
"""


def test_extract_build_id_from_html():
    result = extract_build_id(FAKE_HTML)
    assert result == "XalSUGjxvqXwyKRn4Rjgj"


def test_extract_build_id_raises_when_missing():
    with pytest.raises(ValueError, match="buildId"):
        extract_build_id("<html>no build id here</html>")


@pytest.mark.asyncio
async def test_get_build_id_fetches_and_caches():
    _cache.clear()
    with respx.mock:
        respx.get("https://travel.interpark.com/air").mock(
            return_value=httpx.Response(200, text=FAKE_HTML)
        )
        async with httpx.AsyncClient() as client:
            result = await get_build_id(client)
        assert result == "XalSUGjxvqXwyKRn4Rjgj"
        assert _cache.get("build_id") == "XalSUGjxvqXwyKRn4Rjgj"


@pytest.mark.asyncio
async def test_get_build_id_uses_cache():
    _cache["build_id"] = "cached_id"
    async with httpx.AsyncClient() as client:
        result = await get_build_id(client)
    assert result == "cached_id"
    _cache.clear()
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/infra/test_build_id.py -v
```

Expected: FAIL

- [ ] **Step 3: 구현**

```python
# src/interpark_mcp/infra/build_id.py
import json
import re
import httpx
from interpark_mcp.common.config import INTERPARK_BASE_URL

_cache: dict[str, str] = {}


def extract_build_id(html: str) -> str:
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>([^<]+)</script>', html)
    if not match:
        raise ValueError("Cannot find __NEXT_DATA__ script tag in HTML")
    data = json.loads(match.group(1))
    build_id = data.get("buildId")
    if not build_id:
        raise ValueError("buildId missing from __NEXT_DATA__")
    return build_id


async def get_build_id(client: httpx.AsyncClient) -> str:
    if cached := _cache.get("build_id"):
        return cached
    resp = await client.get(f"{INTERPARK_BASE_URL}/air")
    resp.raise_for_status()
    build_id = extract_build_id(resp.text)
    _cache["build_id"] = build_id
    return build_id


def invalidate_build_id_cache() -> None:
    _cache.pop("build_id", None)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/infra/test_build_id.py -v
```

Expected: 4 passed.

- [ ] **Step 5: 커밋**

```bash
git add src/interpark_mcp/infra/build_id.py tests/infra/test_build_id.py
git commit -m "feat(infra): add Next.js buildId extractor with cache"
```

---

## Task 5: 응답 파서

**Files:**
- Create: `src/interpark_mcp/infra/parser.py`
- Create: `tests/infra/test_parser.py`

API raw dict → 도메인 dataclass 변환. 순수 함수, HTTP 의존 없음.

- [ ] **Step 1: 테스트 작성**

```python
# tests/infra/test_parser.py
from datetime import datetime, timedelta
from interpark_mcp.infra.parser import parse_flight, parse_iso_duration

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
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/infra/test_parser.py -v
```

Expected: FAIL

- [ ] **Step 3: 파서 구현**

```python
# src/interpark_mcp/infra/parser.py
import re
from datetime import datetime, timedelta
from interpark_mcp.core.models import (
    Baggage, Schedule, CardCashback, Benefit, PassengerFare, Fare, Flight,
)


def parse_iso_duration(duration: str) -> timedelta:
    """ISO 8601 duration string → timedelta. PT1H5M, PT20M, PT2H 형식만 지원."""
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/infra/test_parser.py -v
```

Expected: 8 passed.

- [ ] **Step 5: 커밋**

```bash
git add src/interpark_mcp/infra/parser.py tests/infra/test_parser.py
git commit -m "feat(infra): add API response parser"
```

---

## Task 6: InterparkRequester

**Files:**
- Create: `src/interpark_mcp/infra/requester.py`
- Create: `tests/infra/test_requester.py`

인터파크 3단계 플로우 구현. `FlightSearcher` ABC 상속.

- [ ] **Step 1: 테스트 작성**

```python
# tests/infra/test_requester.py
import json
import pytest
import respx
import httpx
from datetime import date
from unittest.mock import patch, AsyncMock
from interpark_mcp.infra.requester import InterparkRequester
from interpark_mcp.infra import build_id as build_id_module

FAKE_SSR_RESPONSE = {
    "pageProps": {
        "dehydratedState": {
            "queries": [
                {
                    "state": {
                        "data": {
                            "key": "DOMESTIC::test-uuid-1234",
                            "data": {"tripType": "ONE_WAY", "routeType": "DOMESTIC"},
                        }
                    }
                }
            ]
        }
    }
}

FAKE_ITEMS = [
    {
        "id": "TW0933L",
        "key": "TW_uuid_0",
        "fares": [{"totalPrice": 68900, "passengerFares": [{"type": "ADULT", "count": 1,
            "airPrice": 30900, "otherTax": 4000, "fuelCharge": 33000,
            "ticketingFee": 1000, "discount": 0, "total": 68900}],
            "tags": [], "benefits": []}],
        "seatAvailability": 9,
        "cabin": "ECONOMY",
        "discountType": "DISCOUNT",
        "schedule": {
            "arrival": "PUS", "arrivalAt": "2026-06-20T12:55:00",
            "departure": "GMP", "departureAt": "2026-06-20T11:50:00",
            "marketingCarrier": "TW",
            "freeBaggage": {"volume": 15, "unit": "WEIGHT_KG"},
            "flightTime": "PT1H5M", "flightNumber": "0933",
        },
    }
]


@pytest.mark.asyncio
async def test_search_domestic_one_way():
    build_id_module._cache["build_id"] = "test-build-id"
    base = "https://travel.interpark.com"

    with respx.mock:
        ssr_url = (
            f"{base}/air/_next/data/test-build-id/search"
            "/a:GMP-a:CJU-20260620.json"
        )
        respx.get(ssr_url).mock(
            return_value=httpx.Response(200, json=FAKE_SSR_RESPONSE)
        )
        respx.get(
            f"{base}/air/air-api/inpark-air-web-api/domestic/flights"
            "/search/DOMESTIC::test-uuid-1234/status"
        ).mock(return_value=httpx.Response(200, json={"status": "COMPLETED"}))

        respx.post(
            f"{base}/air/air-api/inpark-air-web-api/domestic/flights"
            "/search/DOMESTIC::test-uuid-1234"
        ).mock(return_value=httpx.Response(200, json={"items": FAKE_ITEMS}))

        searcher = InterparkRequester()
        flights = await searcher.search_domestic(
            origin="GMP", destination="CJU", departure_date=date(2026, 6, 20)
        )

    assert len(flights) == 1
    assert flights[0].id == "TW0933L"
    assert flights[0].schedule.departure == "GMP"
    build_id_module._cache.clear()
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/infra/test_requester.py -v
```

Expected: FAIL

- [ ] **Step 3: InterparkRequester 구현**

```python
# src/interpark_mcp/infra/requester.py
import asyncio
from datetime import date
import httpx
from interpark_mcp.common.config import (
    INTERPARK_BASE_URL, BROWSER_HEADERS,
    POLL_MAX_ATTEMPTS, POLL_INTERVAL_SECONDS,
    DOMESTIC_CITY_CODES,
)
from interpark_mcp.core.interfaces import FlightSearcher
from interpark_mcp.core.models import Flight
from interpark_mcp.infra.build_id import get_build_id, invalidate_build_id_cache
from interpark_mcp.infra.parser import parse_flight


def _location_prefix(code: str) -> str:
    return "c" if code in DOMESTIC_CITY_CODES else "a"


def _build_route_segment(origin: str, destination: str, dep_date: date) -> str:
    o_prefix = _location_prefix(origin)
    d_prefix = _location_prefix(destination)
    return f"{o_prefix}:{origin}-{d_prefix}:{destination}-{dep_date.strftime('%Y%m%d')}"


def _build_return_segment(origin: str, destination: str, ret_date: date) -> str:
    o_prefix = _location_prefix(destination)
    d_prefix = _location_prefix(origin)
    return f"{o_prefix}:{destination}-{d_prefix}:{origin}-{ret_date.strftime('%Y%m%d')}"


class InterparkRequester(FlightSearcher):
    async def search_domestic(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date | None = None,
        adult: int = 1,
        child: int = 0,
        infant: int = 0,
    ) -> list[Flight]:
        async with httpx.AsyncClient(headers=BROWSER_HEADERS, timeout=30.0) as client:
            search_key = await self._get_search_key(
                client, origin, destination, departure_date, return_date, adult, child, infant
            )
            await self._wait_ready(client, search_key)
            return await self._fetch_results(client, search_key)

    async def _get_search_key(
        self, client: httpx.AsyncClient,
        origin: str, destination: str,
        departure_date: date, return_date: date | None,
        adult: int, child: int, infant: int,
    ) -> str:
        outbound = _build_route_segment(origin, destination, departure_date)
        segments = [outbound]
        if return_date:
            segments.append(_build_return_segment(origin, destination, return_date))

        routes_path = "/".join(segments)
        build_id = await get_build_id(client)

        url = (
            f"{INTERPARK_BASE_URL}/air/_next/data/{build_id}"
            f"/search/{routes_path}.json"
        )
        params = [("cabin", "ALL"), ("adult", adult), ("child", child), ("infant", infant)]
        for seg in segments:
            params.append(("schedules", seg))

        resp = await client.get(url, params=params)

        if resp.status_code in (404, 400):
            invalidate_build_id_cache()
            build_id = await get_build_id(client)
            url = (
                f"{INTERPARK_BASE_URL}/air/_next/data/{build_id}"
                f"/search/{routes_path}.json"
            )
            resp = await client.get(url, params=params)

        resp.raise_for_status()
        data = resp.json()
        return data["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["key"]

    async def _wait_ready(self, client: httpx.AsyncClient, search_key: str) -> None:
        url = (
            f"{INTERPARK_BASE_URL}/air/air-api/inpark-air-web-api"
            f"/domestic/flights/search/{search_key}/status"
        )
        for _ in range(POLL_MAX_ATTEMPTS):
            resp = await client.get(url)
            if resp.json().get("status") != "PENDING":
                return
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        raise TimeoutError(f"Search {search_key} did not complete in time")

    async def _fetch_results(self, client: httpx.AsyncClient, search_key: str) -> list[Flight]:
        url = (
            f"{INTERPARK_BASE_URL}/air/air-api/inpark-air-web-api"
            f"/domestic/flights/search/{search_key}"
        )
        body = {
            "pageNumber": 1,
            "pageSize": 20,
            "filter": {
                "byAirline": None,
                "byDepartureTimes": None,
                "byPaymentMethods": None,
                "byDiscountTypes": None,
                "byCabins": None,
            },
        }
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        return [parse_flight(item) for item in resp.json()["items"]]
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/infra/test_requester.py -v
```

Expected: 1 passed.

- [ ] **Step 5: 커밋**

```bash
git add src/interpark_mcp/infra/requester.py tests/infra/test_requester.py
git commit -m "feat(infra): add InterparkRequester with 3-step search flow"
```

---

## Task 7: Dependencies (DI 팩토리)

**Files:**
- Create: `src/interpark_mcp/dependencies/requester.py`
- Create: `tests/core/test_di.py`

- [ ] **Step 1: 테스트 작성**

```python
# tests/core/test_di.py
from interpark_mcp.dependencies.requester import get_requester
from interpark_mcp.core.interfaces import FlightSearcher
from interpark_mcp.infra.requester import InterparkRequester


def test_get_requester_returns_flight_searcher():
    requester = get_requester()
    assert isinstance(requester, FlightSearcher)


def test_get_requester_returns_interpark_implementation():
    requester = get_requester()
    assert isinstance(requester, InterparkRequester)
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/core/test_di.py -v
```

Expected: FAIL

- [ ] **Step 3: 팩토리 구현**

```python
# src/interpark_mcp/dependencies/requester.py
from interpark_mcp.core.interfaces import FlightSearcher
from interpark_mcp.infra.requester import InterparkRequester


def get_requester() -> FlightSearcher:
    return InterparkRequester()
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/core/test_di.py -v
```

Expected: 2 passed.

- [ ] **Step 5: 커밋**

```bash
git add src/interpark_mcp/dependencies/requester.py tests/core/test_di.py
git commit -m "feat(dependencies): add get_requester DI factory"
```

---

## Task 8: MCP 도구 - 국내선 검색

**Files:**
- Create: `src/interpark_mcp/mcp/tools/domestic.py`
- Create: `tests/mcp/test_domestic.py`

- [ ] **Step 1: 테스트 작성**

```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/mcp/test_domestic.py -v
```

Expected: FAIL

- [ ] **Step 3: MCP 도구 구현**

```python
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/mcp/test_domestic.py -v
```

Expected: 2 passed.

- [ ] **Step 5: 커밋**

```bash
git add src/interpark_mcp/mcp/tools/domestic.py tests/mcp/test_domestic.py
git commit -m "feat(mcp): add search_domestic_flights tool"
```

---

## Task 9: FastMCP 서버 엔트리포인트 + 설치 지원

**Files:**
- Create: `src/interpark_mcp/mcp/server.py`
- Create: `src/interpark_mcp/__main__.py`
- Modify: `pyproject.toml` (scripts 엔트리 추가)

설치 후 `interpark-mcp`, `uvx interpark-mcp`, `python -m interpark_mcp` 세 가지 모두 지원.

- [ ] **Step 1: 서버 구현 (`main()` 포함)**

```python
# src/interpark_mcp/mcp/server.py
from fastmcp import FastMCP
from interpark_mcp.mcp.tools.domestic import search_domestic_flights

mcp = FastMCP("interpark-mcp")
mcp.tool()(search_domestic_flights)


def main() -> None:
    mcp.run()
```

- [ ] **Step 2: `__main__.py` 추가 (`python -m interpark_mcp` 지원)**

```python
# src/interpark_mcp/__main__.py
from interpark_mcp.mcp.server import main

main()
```

- [ ] **Step 3: `pyproject.toml`에 scripts 엔트리 추가**

`[project]` 섹션 아래에 추가:

```toml
[project.scripts]
interpark-mcp = "interpark_mcp.mcp.server:main"
```

- [ ] **Step 4: 패키지 재설치**

```bash
pip install -e ".[dev]"
```

- [ ] **Step 5: 설치 방법별 동작 확인**

```bash
# CLI 스크립트 확인
which interpark-mcp

# 모듈 실행 확인
python -m interpark_mcp --help
```

Expected: 명령어 경로 출력, 오류 없음.

- [ ] **Step 6: 전체 테스트 통과 확인**

```bash
pytest -v
```

Expected: all passed, 0 errors.

- [ ] **Step 7: 커밋**

```bash
git add src/interpark_mcp/mcp/server.py src/interpark_mcp/__main__.py pyproject.toml
git commit -m "feat(mcp): add FastMCP server with pip/uv install support"
```

---

## MCP 클라이언트 설정 (참고)

```json
{
  "mcpServers": {
    "interpark": {
      "command": "uvx",
      "args": ["interpark-mcp"]
    }
  }
}
```

pip 설치 시:
```json
{
  "mcpServers": {
    "interpark": {
      "command": "interpark-mcp"
    }
  }
}
```

---

## Self-Review

**스펙 커버리지:**
- ✅ 프로젝트 셋업 (Task 0)
- ✅ core 모델 (Task 1)
- ✅ core 인터페이스 (Task 2)
- ✅ common config (Task 3)
- ✅ buildId 추출/캐시 (Task 4)
- ✅ 응답 파서 (Task 5)
- ✅ InterparkRequester 3단계 플로우 (Task 6)
- ✅ DI 팩토리 (Task 7)
- ✅ MCP 도구 (Task 8)
- ✅ FastMCP 서버 (Task 9)
- ✅ pip/uv/python -m 설치 지원 (Task 9)
- ✅ buildId 만료 시 재추출 (Task 6 `_get_search_key` 404 처리)
- ✅ 상태 폴링 타임아웃 (Task 6 `_wait_ready`)

**타입 일관성:**
- `FlightSearcher` — Task 2 정의, Task 6/7/8 사용 ✅
- `Flight` — Task 1 정의, Task 5/6/8 사용 ✅
- `get_requester()` — Task 7 정의, Task 8 기본값 사용 ✅
- `parse_flight()` — Task 5 정의, Task 6 사용 ✅
- `extract_build_id()` / `get_build_id()` — Task 4 정의, Task 6 사용 ✅
