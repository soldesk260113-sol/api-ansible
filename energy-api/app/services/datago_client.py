import os
import requests
from fastapi import HTTPException

def call_odcloud(url: str, params: dict, timeout: int = 20) -> dict:
    """
    odcloud(api.odcloud.kr) 계열 호출:
    - 어떤 데이터셋은 Authorization 헤더
    - 어떤 데이터셋은 serviceKey 쿼리를 요구함
    => 둘 다 같이 보내서 통일
    """
    key = os.getenv("DATA_GO_KR_SERVICE_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="DATA_GO_KR_SERVICE_KEY not set")

    p = dict(params or {})
    # ✅ 쿼리 serviceKey도 같이 보냄(이미 있으면 덮지 않음)
    p.setdefault("serviceKey", key)

    try:
        r = requests.get(
            url,
            params=p,
            headers={"Authorization": key},
            timeout=timeout,
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"odcloud request failed: {e}")

    if not r.ok:
        raise HTTPException(status_code=r.status_code, detail=r.text[:500])

    return r.json()

