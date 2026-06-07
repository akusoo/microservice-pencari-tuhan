from fastapi import FastAPI

from app.routers.book import router as book_router

app = FastAPI(title="Book Service")

app.include_router(book_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "book"}
