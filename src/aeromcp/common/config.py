# src/aeromcp/common/config.py

BASE_URL = "https://travel.interpark.com"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": f"{BASE_URL}/air",
}

# 국내 도시코드 → c: prefix 사용. 나머지는 a: prefix.
# SEL(서울)만 도시코드인 이유: GMP(김포) + ICN(인천) 두 공항을 포괄하는 유일한 복수공항 도시.
# a:SEL은 동작하지 않으므로 반드시 c:SEL 사용. 나머지 국내 도시는 단일 공항 → a: prefix.
DOMESTIC_CITY_CODES = {"SEL"}

# 국내선 공항 코드 레퍼런스 (a: prefix 사용)
# GMP: 서울/김포  ICN: 서울/인천  CJU: 제주  PUS: 부산/김해
# KWJ: 광주       MWX: 무안       KUV: 군산  TAE: 대구
# HIN: 진주/사천  RSU: 여수       USN: 울산  WJU: 원주
# CJJ: 청주       KPO: 포항       YNY: 양양

# 검색 상태 폴링 설정
POLL_MAX_ATTEMPTS = 15
POLL_INTERVAL_SECONDS = 1.0
