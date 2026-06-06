from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from jose import JWTError, jwt

from app.circuit_breaker import get_breaker
from app.config import settings
from app.middleware.logging import setup_logger

router = APIRouter()
logger = setup_logger("api-gateway.proxy")

PUBLIC_ROUTES: set[tuple[str, str]] = {
    ("/auth/register", "POST"),
    ("/auth/login", "POST"),
    ("/auth/refresh", "POST"),
}

_STRIP_REQUEST_HEADERS = {"host", "content-length", "transfer-encoding", "connection"}
_STRIP_RESPONSE_HEADERS = {"transfer-encoding", "content-encoding", "connection", "keep-alive"}

SERVICE_MAP: dict[str, str] = {
    "/auth":    settings.auth_service_url,
    "/books":   settings.book_service_url,
    "/members": settings.member_service_url,
    "/loans":   settings.loan_service_url,
    "/fines":   settings.fine_service_url,
}


def _resolve_upstream(path: str) -> Optional[str]:
    for prefix, base_url in SERVICE_MAP.items():
        if path.startswith(prefix):
            return base_url + path
    return None


def _validate_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "access":
            raise JWTError("Wrong token type")
        return payload
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {exc}") from exc


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(request: Request, path: str):
    full_path = f"/{path}"
    target_url = _resolve_upstream(full_path)

    if target_url is None:
        raise HTTPException(status_code=404, detail="No upstream service for this path")

    # ── Circuit breaker check ────────────────────────────────────────────────
    breaker = get_breaker(full_path)
    if not breaker.allow_request():
        logger.warning(
            "circuit_open",
            extra={"service": breaker.name, "path": full_path, "state": breaker.state.value},
        )
        raise HTTPException(
            status_code=503,
            detail=f"Service {breaker.name} temporarily unavailable (circuit open — retry in {breaker.reset_timeout}s)",
        )

    # ── JWT validation (protected routes only) ───────────────────────────────
    extra_headers: dict[str, str] = {}
    if (full_path, request.method.upper()) not in PUBLIC_ROUTES:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        payload = _validate_token(auth_header.split(" ", 1)[1])
        extra_headers["X-User-ID"] = payload.get("sub", "")
        extra_headers["X-User-Role"] = payload.get("role", "")

    # ── Forward request ───────────────────────────────────────────────────────
    request_id = getattr(request.state, "request_id", "")
    forward_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in _STRIP_REQUEST_HEADERS
    }
    forward_headers.update(extra_headers)
    if request_id:
        forward_headers["X-Request-ID"] = request_id

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream = await client.request(
                method=request.method,
                url=target_url,
                headers=forward_headers,
                content=body,
                params=dict(request.query_params),
                cookies=dict(request.cookies),
            )
        breaker.record_success()

    except httpx.ConnectError as exc:
        breaker.record_failure()
        logger.error(
            "upstream_connect_error",
            extra={"service": breaker.name, "path": full_path, "circuit_state": breaker.state.value},
        )
        raise HTTPException(status_code=503, detail=f"Cannot reach {breaker.name}") from exc

    except httpx.TimeoutException as exc:
        breaker.record_failure()
        logger.error(
            "upstream_timeout",
            extra={"service": breaker.name, "path": full_path, "circuit_state": breaker.state.value},
        )
        raise HTTPException(status_code=504, detail=f"{breaker.name} timed out") from exc

    response_headers = {
        k: v for k, v in upstream.headers.items()
        if k.lower() not in _STRIP_RESPONSE_HEADERS
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
    )
