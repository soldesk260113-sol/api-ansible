from fastapi import APIRouter, HTTPException, Query
from app.services.datago_client import call_odcloud
from app.services.db import fetch_all, execute

router = APIRouter(prefix="/gas", tags=["gas"])

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
    page: int = 1,
    perPage: int = 200,
):
    rows = fetch_all(
        """
        SELECT *
        FROM app.energy_gas
        WHERE year = %s
        ORDER BY sido_name
        """,
        (year,),
    )

    if rows:
        return {
            "source": "db",
            "count": len(rows),
            "data": rows,
        }

    try:
        result = call_odcloud(
            ODCLOUD_DATASET_URL,
            params={"page": page, "perPage": perPage, "returnType": "JSON"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    data = result.get("data", [])

    insert_sql = """
        INSERT INTO app.energy_gas
        (year, sido_cd, sido_name, supply_value, unit)
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
    """

    for r in data:
        row_year = int(r.get("연도") or year)

        for sido_name, sido_cd in SIDO_MAP.items():
            v = r.get(sido_name)
            if v in (None, "", "-"):
                continue

            try:
                supply = float(str(v).replace(",", ""))
            except ValueError:
                continue

            execute(
                insert_sql,
                (
                    row_year,
                    sido_cd,
                    sido_name,
                    supply,
                    "unknown",
                ),
            )

    rows = fetch_all(
        """
        SELECT *
        FROM app.energy_gas
        WHERE year = %s
        ORDER BY sido_name
        """,
        (year,),
    )

    return {
        "source": "api→db",
        "count": len(rows),
        "data": rows,
    }

