from fastapi import APIRouter
from app.services.kma_client import call_kma
from app.services.time_rules import ultra_ncst_base_datetime

router = APIRouter()

KMA_URL_ULTRA_NCST = (
    "https://apihub.kma.go.kr/api/typ02/openApi/"
    "VilageFcstInfoService_2.0/getUltraSrtNcst"
)

def simplify_ultra_ncst(data: dict):
    items = data["response"]["body"]["items"]["item"]
    base_date = items[0]["baseDate"]
    base_time = items[0]["baseTime"]
    nx = items[0]["nx"]
    ny = items[0]["ny"]

    value_map = {item["category"]: item["obsrValue"] for item in items}

    def to_float(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return v

    return {
        "baseDate": base_date,
        "baseTime": base_time,
        "nx": nx,
        "ny": ny,
        "temperature_c": to_float(value_map.get("T1H")),
        "humidity_pct": to_float(value_map.get("REH")),
        "rain_1h_mm": to_float(value_map.get("RN1")),
        "precip_type": value_map.get("PTY"),
        "wind_speed_ms": to_float(value_map.get("WSD")),
        "wind_dir_deg": to_float(value_map.get("VEC")),
    }

@router.get("")
def get_weather(nx: int = 60, ny: int = 127):
    # 기존 /weather 호환
    base_date, base_time = ultra_ncst_base_datetime()

    params = {
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }

    data = call_kma(KMA_URL_ULTRA_NCST, params)
    header = data.get("response", {}).get("header", {})
    if header.get("resultCode") != "00":
        return data
    return simplify_ultra_ncst(data)

@router.get("/ultra")
def get_ultra(nx: int = 60, ny: int = 127):
    return get_weather(nx, ny)

