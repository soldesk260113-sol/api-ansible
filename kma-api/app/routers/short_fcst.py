from fastapi import APIRouter, Request
from datetime import datetime, timedelta
import os

from app.services.kma_client import call_kma
from app.services.cache import client as redis_client, make_key, cache_get, cache_set

router = APIRouter()

KMA_URL_SHORT_FCST = (
    "https://apihub.kma.go.kr/api/typ02/openApi/"
    "VilageFcstInfoService_2.0/getVilageFcst"
)

def short_fcst_base_datetime(now=None):
    if now is None:
        now = datetime.now()

    buffer_min = int(os.getenv("KMA_SHORT_BUFFER_MIN", "20"))
    now = now - timedelta(minutes=buffer_min)

    base_hours = [2, 5, 8, 11, 14, 17, 20, 23]
    hh = now.hour

    if hh < 2:
        y = now - timedelta(days=1)
        return y.strftime("%Y%m%d"), "2300"

    cand = max([h for h in base_hours if h <= hh])
    return now.strftime("%Y%m%d"), f"{cand:02d}00"


def _to_float(v):
    try:
        return float(v)
    except Exception:
        return v


def simplify_short_fcst(data, nx, ny):
    items = (
        data.get("response", {})
        .get("body", {})
        .get("items", {})
        .get("item", [])
    )

    if not items:
        return {"nx": nx, "ny": ny, "hourly": []}

    base_date = items[0].get("baseDate")
    base_time = items[0].get("baseTime")

    want = {"TMP", "POP", "SKY", "PTY", "REH", "WSD"}
    bucket = {}

    for it in items:
        fcst_date = it.get("fcstDate")
        fcst_time = it.get("fcstTime")
        cat = it.get("category")
        val = it.get("fcstValue")
        if not fcst_date or not fcst_time or not cat:
            continue
        if cat not in want:
            continue

        key = (fcst_date, fcst_time)
        if key not in bucket:
            bucket[key] = {"fcstDate": fcst_date, "fcstTime": fcst_time}

        if cat in {"TMP", "POP", "REH", "WSD"}:
            bucket[key][cat] = _to_float(val)
        else:
            bucket[key][cat] = val

    hourly = [bucket[k] for k in sorted(bucket.keys())]

    return {
        "baseDate": base_date,
        "baseTime": base_time,
        "nx": nx,
        "ny": ny,
        "hourly": hourly,
    }


@router.get("/short")
def get_short(nx: int = 60, ny: int = 127, request: Request = None):
    prefix = os.getenv("REDIS_PREFIX", "weather")
    ttl = int(os.getenv("REDIS_TTL_SHORT_SECONDS", "3600"))

    raw = str(request.url) if request else f"/weather/short?nx={nx}&ny={ny}"
    k = make_key(prefix, raw)

    # 캐시 장애는 무시하고 진행
    r = None
    try:
        r = redis_client()
        cached = cache_get(r, k)
        if cached is not None:
            return {"cached": True, **cached}
    except Exception:
        r = None

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

    data = call_kma(KMA_URL_SHORT_FCST, params)
    header = data.get("response", {}).get("header", {})

    if header.get("resultCode") != "00":
        return {
            "cached": False,
            "base_date": base_date,
            "base_time": base_time,
            "error": header,
            "response": data.get("response"),
        }

    result = simplify_short_fcst(data, nx, ny)

    try:
        if r is not None:
            cache_set(r, k, result, ttl)
    except Exception:
        pass

    return {"cached": False, **result}

