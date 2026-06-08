from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.fine import router as fine_router

app = FastAPI(title="Fine Service")

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
