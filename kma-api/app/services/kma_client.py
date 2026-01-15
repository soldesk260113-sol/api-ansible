import os
import requests
from fastapi import HTTPException

def call_kma(url: str, params: dict, timeout: int = 20) -> dict:
    auth_key = os.getenv("KMA_AUTHKEY")
    if not auth_key:
        raise HTTPException(status_code=500, detail="KMA_AUTHKEY not set")

    params = dict(params)
    params["authKey"] = auth_key

    try:
        r = requests.get(url, params=params, timeout=timeout)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    data = r.json()

    header = data.get("response", {}).get("header", {})
    if header.get("resultCode") != "00":
        # KMA 에러는 원본 그대로 반환
        return data

    return data

