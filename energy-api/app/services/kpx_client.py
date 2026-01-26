# app/services/kpx_client.py
import os
import hashlib
from fastapi import HTTPException

from app.services.datago_client import call_odcloud
from app.services.cache import client as redis_client, cache_get, cache_set


def _clean_url(v: str) -> str:
    v = v.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1].strip()
    return v


def _make_cache_key(prefix: str, raw: str) -> str:
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:{h}"


def _strip_cache_fields(obj: dict) -> dict:
    if not isinstance(obj, dict):
        return obj
    obj = dict(obj)
    obj.pop("cache", None)
    obj.pop("cache_key", None)
    return obj


def call_kpx_now(page: int = 1, perPage: int = 10) -> dict:
    url = os.getenv("KPX_ODCLOUD_DATASET_URL")
    if not url:
        raise HTTPException(500, "KPX_ODCLOUD_DATASET_URL not set")
    url = _clean_url(url)

    prefix = (os.getenv("REDIS_PREFIX", "energy") or "energy").strip() or "energy"
    ttl = int(os.getenv("KPX_CACHE_TTL", "600"))

    raw_key = f"kpx_now?page={page}&perPage={perPage}"
    cache_key = _make_cache_key(prefix, raw_key)

    # HIT
    try:
        r = redis_client()
        cached = cache_get(r, cache_key)
        if cached is not None:
            cached = _strip_cache_fields(cached)
            return {
                **cached,
                "cache": True,
                "cache_key": cache_key,
            }
    except Exception:
        pass

    # MISS
    data = call_odcloud(url, params={"page": page, "perPage": perPage, "returnType": "JSON"})
    data_to_store = _strip_cache_fields(data)

    try:
        r = redis_client()
        cache_set(r, cache_key, data_to_store, ttl)
    except Exception:
        pass

    return {
        **data_to_store,
        "cache": False,
        "cache_key": cache_key,
    }

