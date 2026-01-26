import os, json, hashlib
from redis import Redis

def client() -> Redis:
    host = os.getenv("REDIS_HOST", "127.0.0.1")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0") or "0")
    password = os.getenv("REDIS_PASSWORD") or None
    return Redis(host=host, port=port, db=db, password=password, decode_responses=True)

def make_key(prefix: str, raw: str) -> str:
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:{h}"

def _strict() -> bool:
    # REDIS_STRICT=1 이면 Redis 장애를 그대로 예외로 올려서 500 유지
    # 기본(0)은 Redis 장애 시 캐시를 그냥 스킵 (None/return)
    return os.getenv("REDIS_STRICT", "0") == "1"

def cache_get(r: Redis, k: str):
    """
    ✅ dict 또는 None만 반환
    - Redis 장애 시: 기본은 None(캐시 미사용)
    - REDIS_STRICT=1 이면 예외 raise
    """
    try:
        v = r.get(k)
        return json.loads(v) if v else None
    except Exception:
        if _strict():
            raise
        return None

def cache_set(r: Redis, k: str, value, ttl: int):
    """
    - Redis 장애 시: 기본은 조용히 스킵
    - REDIS_STRICT=1 이면 예외 raise
    """
    try:
        r.setex(k, ttl, json.dumps(value, ensure_ascii=False))
    except Exception:
        if _strict():
            raise
        return

