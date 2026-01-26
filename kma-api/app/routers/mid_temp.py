# app/routers/mid_temp.py
import os
from fastapi import APIRouter, HTTPException, Query
from psycopg2.extras import Json

from app.services.db import fetch_one, execute
from app.services.kma_client import get_mid_temp as kma_get_mid_temp
from app.services.time_rules import latest_mid_tmfc, prev_mid_tmfc

SCHEMA = os.getenv("DB_SCHEMA", "api")
router = APIRouter()

SQL_SEL = f"""
SELECT reg_id, tm_fc, data, created_at
FROM {SCHEMA}.weather_mid_temp
WHERE reg_id = %s AND tm_fc = %s
LIMIT 1;
"""

SQL_UPSERT = f"""
INSERT INTO {SCHEMA}.weather_mid_temp (reg_id, tm_fc, data)
VALUES (%s, %s, %s)
ON CONFLICT (reg_id, tm_fc)
DO UPDATE SET
  data = EXCLUDED.data,
  created_at = now();
"""

@router.get("/mid/temp", tags=["mid"], summary="Get Mid Temp")
def get_mid_temp(
    regId: str = Query(...),
    tmFc: str | None = Query(None),
):
    tmfc = tmFc or latest_mid_tmfc()

    # 1) DB 조회
    row = fetch_one(SQL_SEL, (regId, tmfc))
    if row:
        return {
            "source": "db",
            "regId": row["reg_id"],
            "tmFc": row["tm_fc"],
            "createdAt": row["created_at"].isoformat() if row.get("created_at") else None,
            "data": row["data"],
        }

    # 2) KMA 호출 (폴백)
    used_tmfc = tmfc
    try:
        payload = kma_get_mid_temp(regId=regId, tmFc=tmfc)
    except Exception:
        tmfc2 = prev_mid_tmfc(tmfc)
        try:
            payload = kma_get_mid_temp(regId=regId, tmFc=tmfc2)
            used_tmfc = tmfc2
        except Exception as e2:
            raise HTTPException(status_code=502, detail=f"KMA upstream error: {e2}")

    # 3) DB 저장
    execute(SQL_UPSERT, (regId, used_tmfc, Json(payload)))

    return {
        "source": "api→db",
        "regId": regId,
        "tmFc": used_tmfc,
        "createdAt": None,
        "data": payload,
    }

