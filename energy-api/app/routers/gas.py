from fastapi import APIRouter, HTTPException
from app.services.datago_client import call_odcloud

router = APIRouter(prefix="/gas", tags=["gas"])

# ✅ 너가 이미 성공 확인한 데이터셋 URL을 그대로 사용 (예시)
ODCLOUD_DATASET_URL = "https://api.odcloud.kr/api/15040818/v1/uddi:0873d163-4ed7-49f9-bf95-8eb5c7e35fad"

@router.get("/sido/year")
def gas_sido_year(page: int = 1, perPage: int = 200):
    """
    국가가스공사 연간 시도별 도시가스 판매 통계현황
    """
    try:
        return call_odcloud(
            ODCLOUD_DATASET_URL,
            params={"page": page, "perPage": perPage, "returnType": "JSON"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

