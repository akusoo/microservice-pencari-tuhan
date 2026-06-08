import logging
import uuid

import httpx

from app.core.config import settings

logger = logging.getLogger("fine_service.member_client")


async def get_member_by_user_id(user_id: uuid.UUID) -> dict:
    url = f"{settings.member_service_url}/members/me"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers={"X-User-ID": str(user_id), "X-User-Role": "member"})
        resp.raise_for_status()
        return resp.json()


async def update_member_status(member_id: uuid.UUID, status: str) -> None:
    url = f"{settings.member_service_url}/members/{member_id}/status"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.patch(url, json={"status": status})
        if resp.status_code not in (200, 201):
            logger.error("Failed to update member status: %s %s", resp.status_code, resp.text)
