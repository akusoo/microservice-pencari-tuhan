from fastapi import FastAPI

from app.routers.member import router as member_router

app = FastAPI(title="Member Service")

app.include_router(member_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "member"}
