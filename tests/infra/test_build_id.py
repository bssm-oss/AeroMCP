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
