import os
import requests
from fastapi import HTTPException

KEPCO_HOUSE_AVE_URL = "https://bigdata.kepco.co.kr/openapi/v1/powerUsage/houseAve.do"

def call_kepco_house_ave(year: int, month: int, metroCd: str, timeout: int = 20) -> dict:
    """
    KEPCO 가구평균 전력사용량 조회 (houseAve)
    - cityCd는 생략
    - 인증: apiKey 쿼리 파라미터
    - ✅ 최종: EMP_API_KEY를 표준 키로 사용 (하위호환: KEPCO_API_KEY도 허용)
    """
    api_key = os.getenv("EMP_API_KEY") or os.getenv("KEPCO_API_KEY") or os.getenv("KEPCO_SERVICE_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="EMP_API_KEY not set (or KEPCO_API_KEY)")

    params = {
        "year": year,
        "month": month,
        "metroCd": metroCd,
        "returnType": "json",
        "apiKey": api_key,
    }

    try:
        r = requests.get(KEPCO_HOUSE_AVE_URL, params=params, timeout=timeout)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"KEPCO request failed: {e}")

    safe_url = r.url.replace(api_key, "***")

    if r.status_code == 200:
        try:
            return {"ok": True, "provider": "KEPCO", "data": r.json()}
        except Exception:
            return {"ok": True, "provider": "KEPCO", "raw": r.text[:2000]}

    return {
        "ok": False,
        "provider": "KEPCO",
        "request_url": safe_url,
        "status_code": r.status_code,
        "text_head": r.text[:500],
    }

