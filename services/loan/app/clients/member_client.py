import uuid

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

_SERVICE_HEADERS = {"X-Internal-Service-Key": settings.internal_service_key}


async def get_member(member_id: uuid.UUID) -> dict:
    url = f"{settings.member_service_url}/members/{member_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=_SERVICE_HEADERS)
        if resp.status_code == 404:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member not found")
        resp.raise_for_status()
        return resp.json()


async def get_member_by_user_id(user_id: uuid.UUID) -> dict:
    url = f"{settings.member_service_url}/members/me"
    headers = {**_SERVICE_HEADERS, "X-User-ID": str(user_id)}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member profile not found")
        resp.raise_for_status()
        return resp.json()
