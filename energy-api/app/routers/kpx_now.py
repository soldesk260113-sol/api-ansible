import os
from fastapi import APIRouter, Query

from app.services.kpx_client import call_kpx_now
from app.services.cache import client, make_key, cache_get, cache_set

router = APIRouter()

@router.get("/now")
def kpx_now(
    page: int = Query(1, ge=1),
    perPage: int = Query(10, ge=1, le=1000),
):
    # env 기반 TTL / prefix
    ttl = int(os.getenv("KPX_CACHE_TTL", "600"))
    prefix = os.getenv("REDIS_PREFIX", "energy")

    # 요청 파라미터를 raw에 포함(요청별 캐시 분리)
    raw = f"kpx_now?page={page}&perPage={perPage}"

    r = client()
    k = make_key(prefix, raw)

    # 1) 캐시 히트
    cached = cache_get(r, k)
    if cached is not None:
        return cached

    # 2) 캐시 미스 -> 외부 호출
    data = call_kpx_now(page=page, perPage=perPage)

    # 3) 저장
    cache_set(r, k, data, ttl)
    return data

