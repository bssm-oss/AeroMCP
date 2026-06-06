# src/interpark_mcp/infra/build_id.py
import json
import re
import httpx
from interpark_mcp.common.config import INTERPARK_BASE_URL

_cache: dict[str, str] = {}


def extract_build_id(html: str) -> str:
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>([^<]+)</script>', html)
    if not match:
        raise ValueError("buildId not found: cannot locate __NEXT_DATA__ script tag in HTML")
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
