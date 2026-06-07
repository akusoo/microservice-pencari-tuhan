from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.member import router as member_router

app = FastAPI(title="Member Service")

# Dev/demo only: lets the static demo UI (served from a different origin) call this
# service directly while gateway/auth aren't wired up yet. Browser traffic in
# production goes through the gateway, which owns CORS for real client origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(member_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "member"}
