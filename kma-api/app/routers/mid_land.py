# app/routers/mid_land.py
import json
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.services.db import fetch_one, execute
from app.services.kma_client import get_mid_land as kma_get_mid_land
from app.services.time_rules import latest_mid_tmfc, prev_mid_tmfc

router = APIRouter()

SQL_SEL = """
SELECT data
FROM app.weather_mid_land
WHERE reg_id = %s AND tm_fc = %s
LIMIT 1;
"""

SQL_UPSERT = """
INSERT INTO app.weather_mid_land (reg_id, tm_fc, base_date, data)
VALUES (%s, %s, %s, %s::jsonb)
ON CONFLICT (reg_id, tm_fc)
DO UPDATE SET
  data = EXCLUDED.data,
  base_date = EXCLUDED.base_date,
  created_at = now();
"""

@router.get("/mid/land", tags=["mid"], summary="Get Mid Land Forecast")
def get_mid_land_forecast(
    regId: str = Query(...),
    tmFc: str | None = Query(None),
):
    tmfc = tmFc or latest_mid_tmfc()
    base_date = date.today()

    # 1) DB 조회
    row = fetch_one(SQL_SEL, (regId, tmfc))
    if row and row.get("data") is not None:
        return row["data"]

    # 2) KMA 호출(폴백)
    try:
        payload = kma_get_mid_land(regId=regId, tmFc=tmfc)
    except Exception:
        tmfc2 = prev_mid_tmfc(tmfc)
        try:
            payload = kma_get_mid_land(regId=regId, tmFc=tmfc2)
            tmfc = tmfc2
        except Exception as e2:
            raise HTTPException(status_code=502, detail=f"KMA upstream error: {e2}")

    # 3) UPSERT
    execute(SQL_UPSERT, (regId, tmfc, base_date, json.dumps(payload, ensure_ascii=False)))

    # 4) 반환(디버그)
    if isinstance(payload, dict):
        payload.setdefault("_meta", {})
        payload["_meta"]["tmFc_used"] = tmfc
    return payload

