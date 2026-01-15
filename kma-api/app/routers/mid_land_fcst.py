from fastapi import APIRouter
from app.services.kma_client import call_kma
from app.services.time_rules import latest_mid_tmfc

router = APIRouter()

KMA_URL_MID_LAND = (
    "https://apihub.kma.go.kr/api/typ02/openApi/"
    "MidFcstInfoService/getMidLandFcst"
)

@router.get("/mid/land")
def get_mid_land_forecast(regId: str, tmFc: str | None = None):
    tmFc = tmFc or latest_mid_tmfc()

    params = {
        "pageNo": 1,
        "numOfRows": 100,
        "dataType": "JSON",
        "regId": regId,
        "tmFc": tmFc,
    }

    return call_kma(KMA_URL_MID_LAND, params)

