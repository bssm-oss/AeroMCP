# AeroMCP

인터파크 국내선 항공권 조회 MCP 서버.

AI 에이전트(Claude, Cursor 등)가 인터파크 항공 API를 통해 국내선 항공편을 검색하고 분석할 수 있게 해주는 [fastmcp](https://github.com/jlowin/fastmcp) 기반 오픈소스 MCP 서버.

## 기능

- 국내선 편도/왕복 항공권 검색
- 전체 항공사 조회 (티웨이, 에어부산, 대한항공 등)
- 운임 상세 정보 (운임, 유류할증료, 공항세, 카드 캐시백 혜택)
- 실시간 잔여석 조회
- **시간대별/항공사별 가격 분석** (평균·최저·최고가)
- **메타데이터** (응답에 포함된 항공사·공항 코드 한글명 제공)

## 설치

### uvx (권장)

```bash
uvx aeromcp
```

### pip

```bash
pip install aeromcp
```

### 직접 실행

```bash
git clone https://github.com/bssm-oss/AeroMCP.git
cd AeroMCP
pip install -e .
aeromcp
```

## MCP 클라이언트 설정

### Claude Desktop / Cursor

`claude_desktop_config.json` 또는 `mcp.json`:

```json
{
  "mcpServers": {
    "aeromcp": {
      "command": "uvx",
      "args": ["aeromcp"]
    }
  }
}
```

pip 설치 시:

```json
{
  "mcpServers": {
    "aeromcp": {
      "command": "aeromcp"
    }
  }
}
```

## 사용 가능한 도구

### `search_domestic_flights`

국내선 항공권을 검색하고 시간대별·항공사별 가격 분석을 반환합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `origin` | string | ✓ | 출발 IATA 코드 (예: `GMP`, `SEL`) |
| `destination` | string | ✓ | 도착 IATA 코드 (예: `CJU`, `PUS`) |
| `departure_date` | string | ✓ | 출발일 `YYYY-MM-DD` |
| `return_date` | string | | 귀국일 `YYYY-MM-DD` (왕복 시) |
| `adult` | int | | 성인 수 (기본값 1) |
| `child` | int | | 소아 수 (기본값 0) |
| `infant` | int | | 유아 수 (기본값 0) |
| `cabin` | string | | 좌석 등급 필터 - `ECONOMY` 또는 `BUSINESS` (기본값 null=전체) |
| `airlines` | string[] | | 항공사 필터 - IATA 코드 목록 예: `["BX","TW"]` (기본값 null=전체) |

**응답 구조:**

```json
{
  "result": [
    {
      "id": "TW0933L",
      "total_price": 68900,
      "departure": "GMP",
      "arrival": "CJU",
      "departure_at": "2026-06-20T11:50:00",
      "arrival_at": "2026-06-20T12:55:00",
      "carrier": "TW",
      "flight_number": "0933",
      "flight_time_minutes": 65,
      "free_baggage_kg": 15,
      "seat_availability": 9,
      "cabin": "ECONOMY",
      "discount_type": "DISCOUNT",
      "cashback": {
        "card_name": "삼성카드",
        "rate": 1.5,
        "amount": 1010,
        "discounted_price": 67890
      }
    }
  ],
  "analysis": {
    "by_time_slot": {
      "morning":   { "count": 4, "avg_price": 72000, "min_price": 68900, "max_price": 76000 },
      "afternoon": { "count": 3, "avg_price": 85000, "min_price": 81000, "max_price": 90000 },
      "evening":   { "count": 2, "avg_price": 95000, "min_price": 92000, "max_price": 98000 }
    },
    "by_airline": {
      "7C": { "count": 3, "avg_price": 71000, "min_price": 68000, "max_price": 75000 },
      "BX": { "count": 3, "avg_price": 80000, "min_price": 76000, "max_price": 84000 },
      "TW": { "count": 3, "avg_price": 88000, "min_price": 85000, "max_price": 92000 }
    }
  },
  "metadata": {
    "carriers": {
      "7C": "제주항공",
      "BX": "에어부산",
      "TW": "티웨이항공"
    },
    "airports": {
      "GMP": "서울/김포",
      "PUS": "부산/김해"
    }
  }
}
```

**시간대 구분:**

| 슬롯 | 범위 |
|------|------|
| `dawn` | 00:00 – 05:59 |
| `morning` | 06:00 – 11:59 |
| `afternoon` | 12:00 – 17:59 |
| `evening` | 18:00 – 23:59 |

### `find_cheapest_roundtrip`

왕복 편도를 각각 검색 후 최저가 조합을 반환합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `origin` | string | ✓ | 출발 IATA 코드 |
| `destination` | string | ✓ | 도착 IATA 코드 |
| `departure_date` | string | ✓ | 출발일 `YYYY-MM-DD` |
| `return_date` | string | ✓ | 귀국일 `YYYY-MM-DD` |
| `adult` | int | | 성인 수 (기본값 1) |
| `child` | int | | 소아 수 (기본값 0) |
| `infant` | int | | 유아 수 (기본값 0) |
| `cabin` | string | | 좌석 등급 필터 - `ECONOMY` 또는 `BUSINESS` (기본값 null=전체) |
| `airlines` | string[] | | 항공사 필터 - IATA 코드 목록 (기본값 null=전체) |
| `top_n` | int | | 반환할 최저가 조합 수 (기본값 5) |

**응답 구조:**

```json
{
  "combinations": [
    {
      "total_price": 155000,
      "outbound": { "id": "BX8816", "departure_at": "2026-07-01T09:00:00", "total_price": 80000, "...": "..." },
      "inbound":  { "id": "BX8806", "departure_at": "2026-07-05T10:00:00", "total_price": 75000, "...": "..." }
    }
  ],
  "outbound_flights": [...],
  "inbound_flights": [...]
}
```

## 공항 코드

| 코드 | 도시/공항 | 비고 |
|------|-----------|------|
| `SEL` | 서울 | 도시 코드 (GMP + ICN 통합) |
| `GMP` | 서울/김포 | |
| `ICN` | 서울/인천 | |
| `CJU` | 제주 | |
| `PUS` | 부산/김해 | |
| `KWJ` | 광주 | |
| `MWX` | 무안 | |
| `KUV` | 군산 | |
| `TAE` | 대구 | |
| `HIN` | 진주/사천 | |
| `RSU` | 여수 | |
| `USN` | 울산 | |
| `WJU` | 원주 | |
| `CJJ` | 청주 | |
| `KPO` | 포항 | |
| `YNY` | 양양 | |

## 아키텍처

```
mcp/          - FastMCP 도구 정의
core/         - 도메인 모델 (dataclass), 추상 인터페이스
infra/        - 항공 API 호출 구현체
common/       - 설정 상수, 브라우저 헤더
dependencies/ - 의존성 주입 팩토리
```

의존 방향: `mcp → core ← infra`

## 개발

```bash
git clone https://github.com/bssm-oss/AeroMCP.git
cd AeroMCP
pip install -e ".[dev]"
pytest
```

## 라이선스

MIT
