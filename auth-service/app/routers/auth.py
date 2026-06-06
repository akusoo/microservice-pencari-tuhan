import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RefreshToken
from app.schemas import UserRegister, UserLogin, UserResponse, TokenResponse, MessageResponse
from app.utils.jwt import create_access_token
from app.utils.password import hash_password, verify_password, hash_token
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    access_token = create_access_token(str(user.id), user.role.value)

    raw_refresh_token = secrets.token_urlsafe(64)
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(refresh_token)
    db.commit()

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=False,  # set True in production (HTTPS)
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 3600,
    )

    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    token_hash = hash_token(refresh_token)
    stored = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.is_revoked == False,  # noqa: E712
    ).first()

    if not stored:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")

    if stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Rotate: revoke old token immediately
    stored.is_revoked = True

    user = db.query(User).filter(User.id == stored.user_id).first()
    if not user or not user.is_active:
        db.commit()
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token(str(user.id), user.role.value)
    new_raw = secrets.token_urlsafe(64)
    new_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_raw),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(new_token)
    db.commit()

    response.set_cookie(
        key="refresh_token",
        value=new_raw,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 3600,
    )

    return TokenResponse(access_token=access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if refresh_token:
        token_hash = hash_token(refresh_token)
        stored = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == current_user.id,
        ).first()
        if stored:
            stored.is_revoked = True
            db.commit()

    response.delete_cookie(key="refresh_token")
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
