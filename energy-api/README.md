# energy-api

FastAPI 기반 에너지(전력/가스/KPX) 데이터 API 서비스.

## Structure
- `app/main.py`: FastAPI entry
- `app/routers/`: power, gas, kpx_now, health 라우터
- `app/services/`: datago/kepco/kpx 클라이언트

## Local run (container)
```bash
podman build -t energy-api:local .
podman rm -f energy-api 2>/dev/null || true
podman run -d --name energy-api -p 8000:8000 --env-file .env energy-api:local
curl -sS http://127.0.0.1:8000/health
