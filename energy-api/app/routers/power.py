from fastapi import APIRouter, Query
from app.services.kepco_client import call_kepco_house_ave
from app.services.db import fetch_all, execute

router = APIRouter(tags=["power"])


@router.get("/monthly")
def power_monthly(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    metroCd: str = Query(..., min_length=1),
):
    """
    /power/monthly?year=2020&month=11&metroCd=11
    """

    # 1️⃣ DB 조회
    rows = fetch_all(
        """
        SELECT *
        FROM app.energy_kepco_monthly
        WHERE year=%s AND month=%s AND metro_cd=%s
        ORDER BY city
        """,
        (year, month, metroCd),
    )

    if rows:
        return {
            "source": "db",
            "count": len(rows),
            "data": rows,
        }

    # 2️⃣ 외부 API 호출
    result = call_kepco_house_ave(year=year, month=month, metroCd=metroCd)
    data = result["data"]["data"]

    # 3️⃣ DB INSERT
    insert_sql = """
        INSERT INTO app.energy_kepco_monthly
        (year, month, metro_cd, metro_name, city, house_cnt, power_usage, bill)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
    """

    for r in data:
        execute(
            insert_sql,
            (
                year,
                month,
                metroCd,
                r["metro"],
                r["city"],
                r["houseCnt"],
                r["powerUsage"],
                r["bill"],
            ),
        )

    # 4️⃣ 다시 DB 조회
    rows = fetch_all(
        """
        SELECT *
        FROM app.energy_kepco_monthly
        WHERE year=%s AND month=%s AND metro_cd=%s
        ORDER BY city
        """,
        (year, month, metroCd),
    )

    return {
        "source": "api→db",
        "count": len(rows),
        "data": rows,
    }

