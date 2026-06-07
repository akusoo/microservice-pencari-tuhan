import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id, require_roles
from app.db.session import get_db
from app.schemas.member import MemberCreate, MemberResponse, MemberStatusUpdate, MemberUpdate
from app.services import member_service

router = APIRouter(prefix="/members", tags=["members"])


@router.get(
    "",
    response_model=list[MemberResponse],
    dependencies=[Depends(require_roles("admin", "librarian"))],
)
async def list_members(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await member_service.list_members(db, skip=skip, limit=limit)


@router.get("/me", response_model=MemberResponse)
async def get_my_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await member_service.get_member_by_user_id(db, uuid.UUID(user_id))


@router.get(
    "/{member_id}",
    response_model=MemberResponse,
    dependencies=[Depends(require_roles("admin", "librarian"))],
)
async def get_member(member_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await member_service.get_member(db, member_id)


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "librarian"))],
)
async def create_member(data: MemberCreate, db: AsyncSession = Depends(get_db)):
    return await member_service.create_member(db, data)


@router.put(
    "/{member_id}",
    response_model=MemberResponse,
    dependencies=[Depends(require_roles("admin", "librarian"))],
)
async def update_member(member_id: uuid.UUID, data: MemberUpdate, db: AsyncSession = Depends(get_db)):
    return await member_service.update_member(db, member_id, data)


@router.patch(
    "/{member_id}/status",
    response_model=MemberResponse,
    dependencies=[Depends(require_roles("admin", "librarian"))],
)
async def update_member_status(
    member_id: uuid.UUID,
    data: MemberStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await member_service.update_status(db, member_id, data)


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
)
async def delete_member(member_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await member_service.delete_member(db, member_id)
