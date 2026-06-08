import uuid

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

_SERVICE_HEADERS = {"X-Internal-Service-Key": settings.internal_service_key}


async def get_book(book_id: uuid.UUID) -> dict:
    url = f"{settings.book_service_url}/books/{book_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=_SERVICE_HEADERS)
        if resp.status_code == 404:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book not found")
        resp.raise_for_status()
        return resp.json()


async def update_stock(book_id: uuid.UUID, delta: int) -> None:
    url = f"{settings.book_service_url}/books/{book_id}/stock"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.patch(url, json={"delta": delta}, headers=_SERVICE_HEADERS)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to update book stock",
            )
