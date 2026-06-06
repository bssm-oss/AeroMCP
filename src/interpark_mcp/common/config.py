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
