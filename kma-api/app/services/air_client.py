# app/services/air_client.py
import os
import httpx

BASE = "https://apis.data.go.kr/B552584/ArpltnInforInqireSvc"
SERVICE_KEY = os.getenv("AIRKOREA_SERVICE_KEY")

def _ensure_key():
    if not SERVICE_KEY:
        raise RuntimeError("AIRKOREA_SERVICE_KEY is missing")

async def fetch_forecast_xml(search_date: str, inform_code: str) -> str:
    """
    예보(등급) XML: getMinuDustFrcstDspth
    """
    _ensure_key()
    url = f"{BASE}/getMinuDustFrcstDspth"
    params = {
        "serviceKey": SERVICE_KEY,
        "searchDate": search_date,     # YYYY-MM-DD
        "InformCode": inform_code,     # PM10 or PM25
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.text

async def fetch_realtime_json(sido_name: str = "서울", num_rows: int = 100, page_no: int = 1) -> dict:
    """
    실시간(수치) JSON: getCtprvnRltmMesureDnsty
    - pm10Value, pm25Value 등이 들어있음
    """
    _ensure_key()
    url = f"{BASE}/getCtprvnRltmMesureDnsty"
    params = {
        "serviceKey": SERVICE_KEY,
        "returnType": "json",
        "sidoName": sido_name,
        "numOfRows": str(num_rows),
        "pageNo": str(page_no),
        "ver": "1.0",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()

