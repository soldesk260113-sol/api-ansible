from fastapi import APIRouter, Query
from app.services.kepco_client import call_kepco_house_ave

router = APIRouter()

@router.get("/monthly")
def power_monthly(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    metroCd: str = Query(..., min_length=1),
):
    """
    /power/monthly?year=2020&month=11&metroCd=11
    cityCd는 사용하지 않음(생략)
    """
    return call_kepco_house_ave(year=year, month=month, metroCd=metroCd)

