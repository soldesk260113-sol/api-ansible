# kma-api

FastAPI 기반 기상청(KMA) 날씨 API 서비스.

## Local run (container)
```bash
podman build -t kma-api:local .
podman run -d --name kma-api -p 8000:8000 --env-file .env kma-api:local
curl -sS http://127.0.0.1:8000/health
