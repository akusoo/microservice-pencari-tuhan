from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.routers.fine import router as fine_router

app = FastAPI(title="Fine Service")

# Exposes GET /metrics (Prometheus format): request count, latency and status
# code per route — no logging involved, just counters/histograms scraped by Prometheus.
Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fine_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "fine"}
