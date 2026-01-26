from psycopg2.extras import Json
import os
from fastapi import APIRouter, Query, HTTPException
from app.services.kepco_client import call_kepco_house_ave
from app.services.db import fetch_one, execute

router = APIRouter(tags=["power"])

SCHEMA = os.getenv("DB_SCHEMA", "api")


@router.get("/monthly")
def power_monthly(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    metroCd: str = Query(..., min_length=1),
):
    """
    /power/monthly?year=2024&month=12&metroCd=11
    DB: api.energy_kepco_monthly(region_code, ym, data, created_at)
    """
    ym = f"{year}{month:02d}"  # YYYYMM

    # 1) DB 조회 (최신 1건)
    row = fetch_one(
        f"""
        SELECT id, region_code, ym, data, created_at
        FROM {SCHEMA}.energy_kepco_monthly
        WHERE region_code = %s AND ym = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (metroCd, ym),
    )

    if row:
        return {
            "source": "db",
            "regionCode": row["region_code"],
            "ym": row["ym"].strip() if isinstance(row["ym"], str) else row["ym"],
            "createdAt": row["created_at"].isoformat() if row.get("created_at") else None,
            "data": row["data"],
        }

    # 2) 외부 API 호출
    try:
        result = call_kepco_house_ave(year=year, month=month, metroCd=metroCd)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    # 3) DB INSERT (원본 jsonb 저장)
    execute(
        f"""
        INSERT INTO {SCHEMA}.energy_kepco_monthly (region_code, ym, data)
        VALUES (%s, %s, %s)
        """,
        (metroCd, ym, Json(result)),
    )

    # 4) 다시 DB 조회
    row = fetch_one(
        f"""
        SELECT id, region_code, ym, data, created_at
        FROM {SCHEMA}.energy_kepco_monthly
        WHERE region_code = %s AND ym = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (metroCd, ym),
    )

    return {
        "source": "api→db",
        "regionCode": row["region_code"],
        "ym": row["ym"].strip() if isinstance(row["ym"], str) else row["ym"],
        "createdAt": row["created_at"].isoformat() if row.get("created_at") else None,
        "data": row["data"],
    }

