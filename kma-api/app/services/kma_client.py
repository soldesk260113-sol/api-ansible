# app/services/kma_client.py
import os
import requests
from typing import Optional
from fastapi import HTTPException


def call_kma(url: str, params: dict, timeout: int = 20) -> dict:
    """
    KMA API 공통 호출 함수.
    """
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
        return data

    return data


def get_mid_temp(
    regId: str,
    tmFc: Optional[str] = None,
    pageNo: int = 1,
    numOfRows: int = 100,
) -> dict:
    """
    중기 기온 조회
    """
    url = "https://apihub.kma.go.kr/api/typ02/openApi/MidFcstInfoService/getMidTa"
    params = {
        "pageNo": pageNo,
        "numOfRows": numOfRows,
        "dataType": "JSON",
        "regId": regId,
    }
    if tmFc:
        params["tmFc"] = tmFc

    return call_kma(url, params, timeout=20)


def get_mid_land(
    regId: str,
    tmFc: Optional[str] = None,
    pageNo: int = 1,
    numOfRows: int = 100,
) -> dict:
    """
    중기 육상 예보 조회
    """
    url = "https://apihub.kma.go.kr/api/typ02/openApi/MidFcstInfoService/getMidLandFcst"
    params = {
        "pageNo": pageNo,
        "numOfRows": numOfRows,
        "dataType": "JSON",
        "regId": regId,
    }
    if tmFc:
        params["tmFc"] = tmFc

    return call_kma(url, params, timeout=20)

