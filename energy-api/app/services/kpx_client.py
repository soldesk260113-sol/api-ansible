import os
from fastapi import HTTPException
from app.services.datago_client import call_odcloud

def _clean_url(v: str) -> str:
    v = v.strip()
    # env에 "..." 또는 '...'로 넣어도 동작하도록
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1].strip()
    return v

def call_kpx_now(page: int = 1, perPage: int = 10) -> dict:
    url = os.getenv("KPX_ODCLOUD_DATASET_URL")
    if not url:
        raise HTTPException(
            status_code=500,
            detail="KPX_ODCLOUD_DATASET_URL not set (set odcloud dataset URL for KPX now power)"
        )

    url = _clean_url(url)

    return call_odcloud(
        url,
        params={"page": page, "perPage": perPage, "returnType": "JSON"},
    )

