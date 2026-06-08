from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.messaging.publisher import publisher
from app.middleware.logging import RequestLoggingMiddleware, setup_logger
from app.routers.auth import router as auth_router

logger = setup_logger("auth-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await publisher.connect(settings.redis_url)
    yield
    await publisher.close()


app = FastAPI(
    title="Auth Service",
    description="Authentication and authorization microservice",
    version="1.0.0",
    lifespan=lifespan,
)

# Exposes GET /metrics (Prometheus format): request count, latency and status
# code per route — no logging involved, just counters/histograms scraped by Prometheus.
Instrumentator().instrument(app).expose(app)

app.add_middleware(RequestLoggingMiddleware, logger=logger)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "auth-service"}
