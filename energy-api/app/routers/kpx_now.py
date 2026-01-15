from fastapi import APIRouter, Query
from app.services.kpx_client import call_kpx_now

router = APIRouter()

@router.get("/now")
def kpx_now(
    page: int = Query(1, ge=1),
    perPage: int = Query(10, ge=1, le=1000),
):
    return call_kpx_now(page=page, perPage=perPage)

