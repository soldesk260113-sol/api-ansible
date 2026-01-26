from psycopg2.extras import Json
import os
from fastapi import APIRouter, HTTPException, Query
from app.services.datago_client import call_odcloud
from app.services.db import fetch_one, execute

router = APIRouter(prefix="/gas", tags=["gas"])

SCHEMA = os.getenv("DB_SCHEMA", "api")

ODCLOUD_DATASET_URL = "https://api.odcloud.kr/api/15040818/v1/uddi:0873d163-4ed7-49f9-bf95-8eb5c7e35fad"

SIDO_MAP = {
    "서울": "11",
    "부산": "26",
    "대구": "27",
    "인천": "28",
    "광주": "29",
    "대전": "30",
    "울산": "31",
    "세종": "36",
    "경기": "41",
    "강원": "42",
    "충북": "43",
    "충남": "44",
    "전북": "45",
    "전남": "46",
    "경북": "47",
    "경남": "48",
    "제주": "50",
}


@router.get("/sido/year")
def gas_sido_year(
    year: int = Query(..., ge=2000, le=2100),
    regionCode: str = Query("11", min_length=1),  # 기본 서울
    page: int = 1,
    perPage: int = 200,
):
    y = str(year)

    # 1) DB 조회 (최신 1건)
    row = fetch_one(
        f"""
        SELECT id, region_code, year, data, created_at
        FROM {SCHEMA}.energy_gas
        WHERE region_code = %s AND year = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (regionCode, y),
    )
    if row:
        return {
            "source": "db",
            "regionCode": row["region_code"],
            "year": row["year"].strip() if isinstance(row["year"], str) else row["year"],
            "createdAt": row["created_at"].isoformat() if row.get("created_at") else None,
            "data": row["data"],
        }

    # 2) 외부 API 호출
    try:
        result = call_odcloud(
            ODCLOUD_DATASET_URL,
            params={"page": page, "perPage": perPage, "returnType": "JSON"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 3) 원본 json 저장 (그냥 통째로)
    execute(
        f"""
        INSERT INTO {SCHEMA}.energy_gas (region_code, year, data)
        VALUES (%s, %s, %s)
        """,
        (regionCode, y, Json(result)),
    )

    # 4) 다시 DB 조회
    row = fetch_one(
        f"""
        SELECT id, region_code, year, data, created_at
        FROM {SCHEMA}.energy_gas
        WHERE region_code = %s AND year = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (regionCode, y),
    )

    return {
        "source": "api→db",
        "regionCode": row["region_code"],
        "year": row["year"].strip() if isinstance(row["year"], str) else row["year"],
        "createdAt": row["created_at"].isoformat() if row.get("created_at") else None,
        "data": row["data"],
    }

