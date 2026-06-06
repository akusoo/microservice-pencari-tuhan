from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.routers.proxy import router as proxy_router

app = FastAPI(
    title="API Gateway",
    description="Library Microservice API Gateway — single entry point",
    version="1.0.0",
)

# Allow the frontend (served from this same origin) plus common dev ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",   # VS Code Live Server
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "api-gateway"}


@app.get("/", include_in_schema=False)
async def frontend():
    return FileResponse("static/index.html")


app.include_router(proxy_router)
