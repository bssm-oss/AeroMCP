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
