import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password, hash_token, verify_password
from app.models.user import RefreshToken, User
from app.schemas.auth import UserRegister


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    if (await db.execute(select(User).where(User.username == data.username))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")
    if (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(username=data.username, email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, username: str, password: str) -> tuple[User, str, str]:
    user = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    access_token = create_access_token(str(user.id), user.role.value)
    raw_refresh = secrets.token_urlsafe(64)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    ))
    await db.commit()
    return user, access_token, raw_refresh


async def rotate_refresh_token(db: AsyncSession, raw_refresh: Optional[str]) -> tuple[str, str]:
    if not raw_refresh:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    stored = (await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(raw_refresh),
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )).scalar_one_or_none()

    if not stored:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")
    if stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    stored.is_revoked = True

    user = await db.get(User, stored.user_id)
    if not user or not user.is_active:
        await db.commit()
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token(str(user.id), user.role.value)
    new_raw = secrets.token_urlsafe(64)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_raw),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    ))
    await db.commit()
    return access_token, new_raw


async def revoke_token(db: AsyncSession, raw_refresh: Optional[str], user_id: uuid.UUID) -> None:
    if not raw_refresh:
        return
    stored = (await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(raw_refresh),
            RefreshToken.user_id == user_id,
        )
    )).scalar_one_or_none()
    if stored:
        stored.is_revoked = True
        await db.commit()
