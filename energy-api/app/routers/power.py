from fastapi import APIRouter, Query, Request
from app.services.kepco_client import call_kepco_house_ave
from app.services.cache import client as redis_client, make_key, cache_get, cache_set
import os

router = APIRouter()

@router.get("/monthly")
def power_monthly(
    request: Request,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    metroCd: str = Query(..., min_length=1),
):
    """
    /power/monthly?year=2020&month=11&metroCd=11
    cityCd는 사용하지 않음(생략)
    """

    # ===== Redis cache (energy monthly) =====
    r = redis_client()
    prefix = os.getenv("REDIS_PREFIX", "energy")
    ttl = int(os.getenv("REDIS_TTL_SECONDS", "600"))  # 에너지는 10분 기본

    raw = str(request.url)
    k = make_key(prefix, raw)

    cached = cache_get(r, k)
    if cached is not None:
        return {"cached": True, **cached}
    # =======================================

    result = call_kepco_house_ave(year=year, month=month, metroCd=metroCd)

    # 성공 응답만 캐싱하고 싶으면 여기서 result의 ok 여부 체크 가능
    cache_set(r, k, result, ttl)
    return {"cached": False, **result}
