# app/routers/dust.py
from __future__ import annotations

import json
import os
import time
import hashlib
from datetime import date

from fastapi import APIRouter, Query

from app.services.air_client import fetch_forecast_xml, fetch_realtime_json
from app.services.air_parser import parse_seoul_grade, parse_seoul_realtime

router = APIRouter(prefix="/dust", tags=["Dust"])

# =========================
# Redis cache (sync client)
# =========================
try:
    import redis  # type: ignore
except Exception:
    redis = None  # redis 미설치/미사용 환경 대비

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

REDIS_PREFIX_DUST = os.getenv("REDIS_PREFIX_DUST", "dust")
REDIS_TTL_DUST_SECONDS = int(os.getenv("REDIS_TTL_DUST_SECONDS", "1800"))

_rds = None
if redis is not None:
    try:
        _rds = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=2,
        )
        # ping은 "최초 사용 시"만 체크(부팅 시 Redis가 잠깐 늦어도 앱이 안 죽게)
    except Exception:
        _rds = None


def _cache_key(endpoint: str, search_date: str, station: str | None) -> str:
    payload = {
        "endpoint": endpoint,
        "search_date": search_date,
        "station": station,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]
    # 예: dust:seoul:<hash>
    return f"{REDIS_PREFIX_DUST}:{endpoint}:{h}"


def _cache_get(key: str) -> tuple[dict | None, int | None]:
    if _rds is None:
        return None, None
    try:
        cached = _rds.get(key)
        if not cached:
            return None, None
        data = json.loads(cached)
        ttl = _rds.ttl(key)
        return data, ttl
    except Exception:
        return None, None


def _cache_set(key: str, value: dict, ttl_seconds: int) -> None:
    if _rds is None:
        return
    try:
        _rds.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False))
    except Exception:
        return


async def _one(kind: str, search_date: str, station: str | None):
    """
    kind: "PM10" | "PM25"
    search_date: "YYYY-MM-DD"
    station: 특정 측정소명(없으면 서울 평균)
    """
    out = {
        "kind": kind,
        "forecast": {"ok": False},
        "realtime": {"ok": False},
    }

    # 1) 예보(등급) - 실패해도 500 내지 말고 error로 내린다
    try:
        xml = await fetch_forecast_xml(search_date, kind)
        out["forecast"] = parse_seoul_grade(xml, search_date)
    except Exception as e:
        out["forecast"] = {
            "ok": False,
            "reason": "FETCH_FORECAST_ERROR",
            "error": str(e),
        }

    # 2) 실시간(수치) - 실패해도 500 내지 말고 error로 내린다
    try:
        rt = await fetch_realtime_json("서울", 100, 1)
        out["realtime"] = parse_seoul_realtime(rt, kind, station=station)
    except Exception as e:
        out["realtime"] = {
            "ok": False,
            "reason": "FETCH_REALTIME_ERROR",
            "error": str(e),
        }

    return out


@router.get("/seoul")
async def seoul(
    search_date: str = Query(default_factory=lambda: date.today().isoformat()),
    station: str | None = Query(default=None, description="특정 측정소명(예: 중구). 없으면 서울 평균"),
):
    # ---------- cache hit ----------
    key = _cache_key("seoul", search_date, station)
    cached, ttl = _cache_get(key)
    if cached is not None:
        cached["source"] = "cache"
        cached["cache_key"] = key
        cached["ttl"] = ttl
        return cached

    t0 = time.time()

    pm10 = await _one("PM10", search_date, station)
    pm25 = await _one("PM25", search_date, station)

    # 한쪽이라도 실패면 디버깅 쉽게 원본 그대로
    if (
        not pm10["forecast"].get("ok")
        or not pm25["forecast"].get("ok")
        or not pm10["realtime"].get("ok")
        or not pm25["realtime"].get("ok")
    ):
        result = {
            "ok": False,
            "date": search_date,
            "station": station,
            "pm10": pm10,
            "pm25": pm25,
        }
        # 실패 응답은 캐시 안 함(원하면 짧게 캐시도 가능)
        result["source"] = "api"
        result["cache_key"] = key
        result["ttl"] = None
        result["took_ms"] = round((time.time() - t0) * 1000, 1)
        return result

    # 둘 다 성공했을 때만 깔끔한 응답
    result = {
        "ok": True,
        "date": search_date,
        "dataTime_forecast": pm10["forecast"]["dataTime"],
        "dataTime_realtime": pm10["realtime"]["dataTime"],
        "pm10": {
            "grade": pm10["forecast"]["seoulGrade"],
            "value": pm10["realtime"]["value"],
        },
        "pm25": {
            "grade": pm25["forecast"]["seoulGrade"],
            "value": pm25["realtime"]["value"],
        },
        "station": station,
        "realtime_agg": None if station else pm10["realtime"].get("agg"),
    }

    # ---------- cache set ----------
    _cache_set(key, result, REDIS_TTL_DUST_SECONDS)

    result["source"] = "api"
    result["cache_key"] = key
    result["ttl"] = REDIS_TTL_DUST_SECONDS
    result["took_ms"] = round((time.time() - t0) * 1000, 1)
    return result


@router.get("/seoul/pm10")
async def seoul_pm10(
    search_date: str = Query(default_factory=lambda: date.today().isoformat()),
    station: str | None = Query(default=None, description="특정 측정소명(예: 중구). 없으면 서울 평균"),
):
    # ---------- cache hit ----------
    key = _cache_key("seoul_pm10", search_date, station)
    cached, ttl = _cache_get(key)
    if cached is not None:
        cached["source"] = "cache"
        cached["cache_key"] = key
        cached["ttl"] = ttl
        return cached

    t0 = time.time()
    result_raw = await _one("PM10", search_date, station)

    # 실패해도 500 금지: ok:false로 내려줌
    if not result_raw["forecast"].get("ok") or not result_raw["realtime"].get("ok"):
        result = {
            "ok": False,
            "date": search_date,
            "station": station,
            "pm10": result_raw,
        }
        result["source"] = "api"
        result["cache_key"] = key
        result["ttl"] = None
        result["took_ms"] = round((time.time() - t0) * 1000, 1)
        return result

    result = {
        "ok": True,
        "date": search_date,
        "station": station,
        "dataTime_forecast": result_raw["forecast"]["dataTime"],
        "dataTime_realtime": result_raw["realtime"]["dataTime"],
        "pm10": {
            "grade": result_raw["forecast"]["seoulGrade"],
            "value": result_raw["realtime"]["value"],
        },
        "realtime_agg": None if station else result_raw["realtime"].get("agg"),
    }

    _cache_set(key, result, REDIS_TTL_DUST_SECONDS)

    result["source"] = "api"
    result["cache_key"] = key
    result["ttl"] = REDIS_TTL_DUST_SECONDS
    result["took_ms"] = round((time.time() - t0) * 1000, 1)
    return result


@router.get("/seoul/pm25")
async def seoul_pm25(
    search_date: str = Query(default_factory=lambda: date.today().isoformat()),
    station: str | None = Query(default=None, description="특정 측정소명(예: 중구). 없으면 서울 평균"),
):
    # ---------- cache hit ----------
    key = _cache_key("seoul_pm25", search_date, station)
    cached, ttl = _cache_get(key)
    if cached is not None:
        cached["source"] = "cache"
        cached["cache_key"] = key
        cached["ttl"] = ttl
        return cached

    t0 = time.time()
    result_raw = await _one("PM25", search_date, station)

    if not result_raw["forecast"].get("ok") or not result_raw["realtime"].get("ok"):
        result = {
            "ok": False,
            "date": search_date,
            "station": station,
            "pm25": result_raw,
        }
        result["source"] = "api"
        result["cache_key"] = key
        result["ttl"] = None
        result["took_ms"] = round((time.time() - t0) * 1000, 1)
        return result

    result = {
        "ok": True,
        "date": search_date,
        "station": station,
        "dataTime_forecast": result_raw["forecast"]["dataTime"],
        "dataTime_realtime": result_raw["realtime"]["dataTime"],
        "pm25": {
            "grade": result_raw["forecast"]["seoulGrade"],
            "value": result_raw["realtime"]["value"],
        },
        "realtime_agg": None if station else result_raw["realtime"].get("agg"),
    }

    _cache_set(key, result, REDIS_TTL_DUST_SECONDS)

    result["source"] = "api"
    result["cache_key"] = key
    result["ttl"] = REDIS_TTL_DUST_SECONDS
    result["took_ms"] = round((time.time() - t0) * 1000, 1)
    return result

