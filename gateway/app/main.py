from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.routers.proxy import router as proxy_router
from app.middleware.logging import RequestLoggingMiddleware, setup_logger
from app.circuit_breaker import get_all_breakers

logger = setup_logger("gateway")

app = FastAPI(
    title="API Gateway",
    description="Library Microservice API Gateway — single entry point",
    version="1.0.0",
)

# Exposes GET /metrics (Prometheus format): request count, latency and status
# code per route — no logging involved, just counters/histograms scraped by Prometheus.
Instrumentator().instrument(app).expose(app)

app.add_middleware(RequestLoggingMiddleware, logger=logger)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",       # frontend service
        "http://127.0.0.1:3000",
        "http://localhost:5500",       # VS Code Live Server
        "http://127.0.0.1:5500",
        "http://localhost:8080",       # direct gateway access
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "gateway"}


@app.get("/admin/circuit-breakers", tags=["admin"])
async def circuit_breaker_status():
    return {name: cb.status() for name, cb in get_all_breakers().items()}


app.include_router(proxy_router)
