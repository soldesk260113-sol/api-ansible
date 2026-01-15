from fastapi import FastAPI

from app.routers.health import router as health_router
from app.routers.gas import router as gas_router
from app.routers.power import router as power_router
from app.routers.kpx_now import router as kpx_now_router

app = FastAPI(title="Energy API", version="1.0.0")

# /health
app.include_router(health_router)

# /gas/...
app.include_router(gas_router)

# /power/...
app.include_router(power_router, prefix="/power", tags=["power"])

# /kpx/...
app.include_router(kpx_now_router, prefix="/kpx", tags=["kpx"])

