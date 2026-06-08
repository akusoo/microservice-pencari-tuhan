from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.loan import router as loan_router

app = FastAPI(title="Loan Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(loan_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "loan"}
