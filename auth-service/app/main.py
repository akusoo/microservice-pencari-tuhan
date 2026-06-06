from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.middleware.logging import RequestLoggingMiddleware, setup_logger

logger = setup_logger("auth-service")

app = FastAPI(
    title="Auth Service",
    description="Authentication and authorization microservice",
    version="1.0.0",
)

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
