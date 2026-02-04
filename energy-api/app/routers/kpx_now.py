from fastapi import APIRouter, Query
from app.services.kpx_client import call_kpx_now

router = APIRouter()

@router.get("/now")
def kpx_now(
    page: int = Query(1, ge=1),
    perPage: int = Query(10, ge=1, le=1000),
):
    # ✅ KPX 캐시는 services(kpx_client)에서 단일 관리
    # router에서 Redis를 또 적용하면 "cache": false가 저장되어 다음 요청에도 고정되는 문제가 생김
    return call_kpx_now(page=page, perPage=perPage)
