import logging
import uuid

import httpx

from app.core.config import settings

logger = logging.getLogger("loan_service.fine_client")


async def create_fine(loan_id: uuid.UUID, member_id: uuid.UUID, amount: float) -> None:
    url = f"{settings.fine_service_url}/fines"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json={
            "loan_id": str(loan_id),
            "member_id": str(member_id),
            "amount": amount,
        })
        if resp.status_code not in (200, 201):
            logger.error("Failed to create fine: %s %s", resp.status_code, resp.text)
