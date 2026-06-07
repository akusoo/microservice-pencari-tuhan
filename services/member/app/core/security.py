# Downstream services trust X-User-ID and X-User-Role headers injected by the gateway.
# JWT re-validation is not done here.

import uuid

from fastapi import Depends, Header, HTTPException, status


def get_current_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> uuid.UUID:
    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid X-User-ID header")


def get_current_user_role(x_user_role: str = Header(..., alias="X-User-Role")) -> str:
    return x_user_role


def require_roles(*allowed_roles: str):
    def checker(role: str = Depends(get_current_user_role)) -> str:
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return role

    return checker
