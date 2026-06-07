from jose import JWTError, jwt
from fastapi import HTTPException

from app.core.config import settings


def decode_token(token: str) -> dict:
    """Validate a Bearer JWT and return its payload. Raises 401 HTTPException on failure."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "access":
            raise JWTError("Wrong token type")
        return payload
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {exc}") from exc
