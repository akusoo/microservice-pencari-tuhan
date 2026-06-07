import uuid

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.schemas.member import MemberCreate, MemberStatusUpdate, MemberUpdate


async def list_members(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[Member]:
    result = await db.execute(select(Member).order_by(Member.full_name).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_member(db: AsyncSession, member_id: uuid.UUID) -> Member:
    member = await db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return member


async def get_member_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Member:
    result = await db.execute(select(Member).where(Member.user_id == user_id))
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member profile not found for this user")
    return member


async def create_member(db: AsyncSession, data: MemberCreate) -> Member:
    existing = await db.execute(
        select(Member).where(or_(Member.user_id == data.user_id, Member.email == data.email))
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A member already exists for this user or email",
        )

    member = Member(**data.model_dump())
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def update_member(db: AsyncSession, member_id: uuid.UUID, data: MemberUpdate) -> Member:
    member = await get_member(db, member_id)
    changes = data.model_dump(exclude_unset=True)

    if "email" in changes and changes["email"] != member.email:
        existing = await db.execute(select(Member).where(Member.email == changes["email"]))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    for field, value in changes.items():
        setattr(member, field, value)

    await db.commit()
    await db.refresh(member)
    return member


async def update_status(db: AsyncSession, member_id: uuid.UUID, data: MemberStatusUpdate) -> Member:
    member = await get_member(db, member_id)
    member.status = data.status
    await db.commit()
    await db.refresh(member)
    return member


async def delete_member(db: AsyncSession, member_id: uuid.UUID) -> None:
    member = await get_member(db, member_id)
    await db.delete(member)
    await db.commit()
