# tests/infra/test_requester.py
import pytest
import respx
import httpx
from datetime import date
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
