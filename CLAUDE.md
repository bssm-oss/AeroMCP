# interpark-mcp

인터파크 항공권 조회 MCP 서버 (오픈소스).

## 목적

fastmcp 기반 MCP 서버. 인터파크 항공 API를 래핑해 AI 에이전트가 국내선/국제선 항공권을 조회할 수 있게 함.

## 아키텍처

```
mcp/          - MCP 도구 정의 (fastmcp @mcp.tool 데코레이터)
core/         - 도메인 모델 (dataclass), 추상 인터페이스
infra/        - 인터파크 API 호출 구현체
common/       - 공통 유틸, config, 상수
dependencies/ - 컴포지트 루트. 함수 기반 의존성 주입 팩토리
```

의존 방향: `mcp → core ← infra`. infra가 core 추상 클래스를 구현.  
`dependencies`는 core + infra 모두 참조 가능. 다른 레이어는 `dependencies`만 바라봄.

## 의존성 주입 컨벤션

`dependencies/`에 팩토리 함수 + `Annotated[추상타입, Depends(팩토리)]` 별칭 정의 (fastmcp DI, `uncalled_for.Depends` 기반):

```python
# dependencies/requester.py
from typing import Annotated
from uncalled_for import Depends
from aeromcp.core.interfaces import FlightSearcher as _FlightSearcher
from aeromcp.infra.requester import AirRequester


def get_requester() -> _FlightSearcher:
    return AirRequester()


FlightSearcher = Annotated[_FlightSearcher, Depends(get_requester)]

# mcp/tools/search.py
from aeromcp.dependencies.requester import FlightSearcher

async def search_flights(
    origin: str,
    destination: str,
    date: str,
    requester: FlightSearcher,
) -> list[Flight]:
    ...
```

- 별칭이 구체 구현체 바인딩 → 호출 측은 core 추상 타입만 앎 (단, import는 `dependencies`에서)
- fastmcp가 tool 스키마에서 `requester` 자동 제외, 호출 시 `Depends` 통해 주입
- 직접 호출(테스트 등) 시엔 fastmcp 컨텍스트 밖이라 기본값 없음 → `requester=mock` 명시 필수
- `get_*` 함수는 순수 팩토리. 상태 없음, 매번 새 인스턴스 또는 싱글턴 반환
- 시그니처 순서 주의: `requester`는 기본값 없는 파라미터이므로 기본값 있는 파라미터들보다 앞에 위치해야 함 (Python 문법 제약)

## 인터파크 API 플로우 (국내선)

검색 세션 키 획득 → 상태 폴링 → 결과 조회 순서.

**1단계: 검색 세션 키 (`DOMESTIC::uuid`) 획득**

Next.js SSR 엔드포인트 호출:
```
GET https://travel.interpark.com/air/_next/data/{buildId}/search/{routes}.json
    ?cabin=ALL&adult=1&child=0&infant=0&schedules={encoded_routes}
```

- `buildId`: HTML `<script id="__NEXT_DATA__">` 파싱으로 추출
- `routes` path 형식: `c:SEL-a:PUS-20260620/a:PUS-c:SEL-20260622`
  - 편도: `a:GMP-a:CJU-20260620`
  - SEL만 `c:` prefix (GMP/ICN 두 공항 포괄하는 도시코드). 나머지 국내 공항은 모두 `a:` prefix.
- 응답 경로: `pageProps.dehydratedState.queries[0].state.data.key`

**2단계: 상태 폴링**

```
GET /air/air-api/inpark-air-web-api/domestic/flights/search/{key}/status
→ { "status": "PENDING" | ... }
```

**3단계: 결과 조회**

```
POST /air/air-api/inpark-air-web-api/domestic/flights/search/{key}
Body: { "pageNumber": 1, "pageSize": 20, "filter": { "byAirline": null, ... } }
```

자세한 응답 스키마: `.interpark/domestic-flight-search.md` 참조.

## 핵심 규칙

- `core`는 인터파크 의존성 없음. 순수 Python dataclass + ABC.
- `common`은 인터파크 의존성 없음. 범용 유틸만.
- `infra`에서 HTTP 호출 시 `User-Agent` 브라우저 헤더 필수 (없으면 차단됨).
- `buildId`는 캐시하되 HTTP 4xx 시 재추출.
- 모든 가격 단위: 원(KRW) 정수.
- 시각 필드: ISO 8601, TZ 없음 (한국 로컬 시각).
- DI 팩토리 함수명: `get_{추상클래스명_snake_case}` 형식.
