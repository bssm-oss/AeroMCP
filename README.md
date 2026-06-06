# AeroMCP

인터파크 국내선 항공권 조회 MCP 서버.

AI 에이전트(Claude, Cursor 등)가 인터파크 항공 API를 통해 국내선 항공편을 검색할 수 있게 해주는 [fastmcp](https://github.com/jlowin/fastmcp) 기반 오픈소스 MCP 서버.

## 기능

- 국내선 편도/왕복 항공권 검색
- 전체 항공사 조회 (티웨이, 에어부산, 대한항공 등)
- 운임 상세 정보 (운임, 유류할증료, 공항세, 카드 캐시백 혜택)
- 실시간 잔여석 조회

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
interpark-mcp
```

## MCP 클라이언트 설정

### Claude Desktop / Cursor

`claude_desktop_config.json` 또는 `mcp.json`:

```json
{
  "mcpServers": {
    "interpark": {
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
    "interpark": {
      "command": "interpark-mcp"
    }
  }
}
```

## 사용 가능한 도구

### `search_domestic_flights`

국내선 항공권을 검색합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `origin` | string | ✓ | 출발 IATA 코드 (예: `GMP`, `SEL`) |
| `destination` | string | ✓ | 도착 IATA 코드 (예: `CJU`, `PUS`) |
| `departure_date` | string | ✓ | 출발일 `YYYY-MM-DD` |
| `return_date` | string | | 귀국일 `YYYY-MM-DD` (왕복 시) |
| `adult` | int | | 성인 수 (기본값 1) |
| `child` | int | | 소아 수 (기본값 0) |
| `infant` | int | | 유아 수 (기본값 0) |

**응답 필드:**

```json
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
infra/        - 인터파크 API 호출 구현체
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
