import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import member_client
from app.models.fine import Fine
from app.schemas.fine import FineCreate


async def create_fine(db: AsyncSession, data: FineCreate) -> Fine:
    existing = await db.execute(select(Fine).where(Fine.loan_id == data.loan_id))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Fine already exists for this loan",
        )

    fine = Fine(**data.model_dump())
    db.add(fine)
    await db.commit()
    await db.refresh(fine)
    return fine


async def pay_fine(db: AsyncSession, fine_id: uuid.UUID) -> Fine:
    fine = await get_fine(db, fine_id)

    if fine.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fine is already paid",
        )

    fine.is_paid = True
    fine.paid_at = datetime.now(timezone.utc)

    await member_client.update_member_status(fine.member_id, "active")

    await db.commit()
    await db.refresh(fine)
    return fine


async def list_fines(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[Fine]:
    result = await db.execute(
        select(Fine).order_by(Fine.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_fine(db: AsyncSession, fine_id: uuid.UUID) -> Fine:
    fine = await db.get(Fine, fine_id)
    if fine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fine not found")
    return fine


async def get_unpaid_fines(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[Fine]:
    result = await db.execute(
        select(Fine)
        .where(Fine.is_paid == False)
        .order_by(Fine.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_fines_by_member_id(db: AsyncSession, member_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[Fine]:
    result = await db.execute(
        select(Fine)
        .where(Fine.member_id == member_id)
        .order_by(Fine.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
