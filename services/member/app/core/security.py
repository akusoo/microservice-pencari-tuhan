from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings


def _decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise JWTError("Wrong token type")
        return payload
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {exc}") from exc


def get_auth_context(
    authorization: Optional[str] = Header(None),
    x_internal_service_key: Optional[str] = Header(None, alias="X-Internal-Service-Key"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict:
    """
    Defense in depth: validate the caller's identity on every request.

    Accepts one of two valid origins:
      1. Internal service call  — X-Internal-Service-Key matches the shared secret.
      2. User request via gateway — Authorization: Bearer <jwt> is valid.
    """
    if x_internal_service_key is not None:
        if x_internal_service_key != settings.internal_service_key:
            raise HTTPException(status_code=401, detail="Invalid internal service key")
        return {"user_id": x_user_id, "role": x_user_role or "service", "is_service": True}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    payload = _decode_jwt(authorization[7:])
    return {"user_id": payload.get("sub"), "role": payload.get("role", ""), "is_service": False}


def get_current_user_id(ctx: dict = Depends(get_auth_context)) -> str:
    user_id = ctx.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User identity not available")
    return user_id


def get_current_user_role(ctx: dict = Depends(get_auth_context)) -> str:
    return ctx["role"]


def require_roles(*allowed_roles: str):
    def checker(ctx: dict = Depends(get_auth_context)) -> str:
        # Internal service calls are trusted — bypass role restrictions.
        if ctx.get("is_service"):
            return ctx["role"]
        role = ctx["role"]
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return role

    return checker
