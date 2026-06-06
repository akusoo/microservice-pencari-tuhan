from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.config import settings


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verify_access_token(token: str) -> dict:
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
    return payload
