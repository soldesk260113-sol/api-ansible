from fastapi import APIRouter, Request
from app.services.kma_client import call_kma
from app.services.time_rules import ultra_ncst_base_datetime
from app.services.cache import client as redis_client, make_key, cache_get, cache_set
import os

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
def get_weather(nx: int = 60, ny: int = 127, request: Request = None):
    # ===== Redis cache (ultra nowcast) =====
    r = redis_client()
    prefix = os.getenv("REDIS_PREFIX", "weather")
    ttl = int(os.getenv("REDIS_TTL_SECONDS", "60"))

    # request가 있으면 실제 URL 전체를 키로 쓰고,
    # 내부 함수 호출(request=None)일 땐 파라미터 기반으로 키를 만든다.
    raw = str(request.url) if request else f"/weather?nx={nx}&ny={ny}"
    k = make_key(prefix, raw)

    cached = cache_get(r, k)
    if cached is not None:
        return {"cached": True, **cached}
    # ======================================

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
        # 에러 응답은 캐싱하지 않음
        return data

    result = simplify_ultra_ncst(data)

    # 성공 응답만 캐싱
    cache_set(r, k, result, ttl)
    return {"cached": False, **result}

@router.get("/ultra")
def get_ultra(nx: int = 60, ny: int = 127, request: Request = None):
    return get_weather(nx, ny, request)
