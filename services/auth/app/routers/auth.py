from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.messaging import events
from app.messaging.publisher import publisher
from app.models.user import User
from app.schemas.auth import MessageResponse, TokenResponse, UserLogin, UserRegister, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = dict(
    key="refresh_token",
    httponly=True,
    secure=False,
    samesite="lax",
    max_age=settings.refresh_token_expire_days * 24 * 3600,
)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(db, data)
    await publisher.publish(events.USER_REGISTERED, {
        "user_id": str(user.id), "username": user.username,
        "email": user.email, "role": user.role.value,
    })
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    user, access_token, raw_refresh = await auth_service.login_user(db, data.username, data.password)
    response.set_cookie(**_REFRESH_COOKIE, value=raw_refresh)
    await publisher.publish(events.USER_LOGGED_IN, {"user_id": str(user.id), "username": user.username})
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    access_token, new_raw = await auth_service.rotate_refresh_token(db, refresh_token)
    response.set_cookie(**_REFRESH_COOKIE, value=new_raw)
    return TokenResponse(access_token=access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.revoke_token(db, refresh_token, current_user.id)
    response.delete_cookie(key="refresh_token")
    await publisher.publish(events.USER_LOGGED_OUT, {"user_id": str(current_user.id)})
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
