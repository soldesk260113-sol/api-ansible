from fastapi import APIRouter
from app.services.kma_client import call_kma
from app.services.time_rules import short_fcst_base_datetime

router = APIRouter()

KMA_URL_SHORT_FCST = (
    "https://apihub.kma.go.kr/api/typ02/openApi/"
    "VilageFcstInfoService_2.0/getVilageFcst"
)

@router.get("/short")
def get_short_forecast(nx: int = 60, ny: int = 127, base_date: str | None = None, base_time: str | None = None):
    if not base_date or not base_time:
        base_date, base_time = short_fcst_base_datetime()

    params = {
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }

    # 여기서는 원본 그대로 반환(필요하면 너처럼 simplify 추가 가능)
    return call_kma(KMA_URL_SHORT_FCST, params)

