import os, json, hashlib
from redis import Redis

def client() -> Redis:
    host = os.getenv("REDIS_HOST", "127.0.0.1")
    port = int(os.getenv("REDIS_PORT", "6379"))
    return Redis(host=host, port=port, decode_responses=True)

def make_key(prefix: str, raw: str) -> str:
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:{h}"

def cache_get(r: Redis, k: str):
    v = r.get(k)
    return json.loads(v) if v else None

def cache_set(r: Redis, k: str, value, ttl: int):
    r.setex(k, ttl, json.dumps(value, ensure_ascii=False))
