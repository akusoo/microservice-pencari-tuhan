import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import member_client
from app.core.security import get_current_user_id, require_roles
from app.db.session import get_db
from app.schemas.fine import FineCreate, FineResponse
from app.services import fine_service

router = APIRouter(prefix="/fines", tags=["fines"])


@router.post("", response_model=FineResponse, status_code=status.HTTP_201_CREATED)
async def create_fine(data: FineCreate, db: AsyncSession = Depends(get_db)):
    return await fine_service.create_fine(db, data)


@router.get(
    "",
    response_model=list[FineResponse],
    dependencies=[Depends(require_roles("admin", "librarian"))],
)
async def list_fines(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await fine_service.list_fines(db, skip=skip, limit=limit)


@router.get("/me", response_model=list[FineResponse])
async def get_my_fines(
    user_id: uuid.UUID = Depends(get_current_user_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    member = await member_client.get_member_by_user_id(user_id)
    return await fine_service.get_fines_by_member_id(db, member["id"], skip=skip, limit=limit)


@router.get(
    "/unpaid",
    response_model=list[FineResponse],
    dependencies=[Depends(require_roles("admin", "librarian"))],
)
async def get_unpaid_fines(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await fine_service.get_unpaid_fines(db, skip=skip, limit=limit)


@router.get("/{fine_id}", response_model=FineResponse)
async def get_fine(fine_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await fine_service.get_fine(db, fine_id)


@router.patch("/{fine_id}/pay", response_model=FineResponse)
async def pay_fine(fine_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await fine_service.pay_fine(db, fine_id)
