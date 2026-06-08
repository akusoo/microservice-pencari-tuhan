import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import member_client
from app.core.security import get_current_user_id, require_roles
from app.db.session import get_db
from app.schemas.loan import LoanCreate, LoanExtend, LoanResponse
from app.services import loan_service

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def create_loan(data: LoanCreate, db: AsyncSession = Depends(get_db)):
    return await loan_service.create_loan(db, data)


@router.get(
    "",
    response_model=list[LoanResponse],
    dependencies=[Depends(require_roles("admin", "librarian"))],
)
async def list_loans(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.list_loans(db, skip=skip, limit=limit)


@router.get("/me", response_model=list[LoanResponse])
async def get_my_loans(
    user_id: uuid.UUID = Depends(get_current_user_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    member = await member_client.get_member_by_user_id(user_id)
    return await loan_service.get_loans_by_member_id(db, member["id"], skip=skip, limit=limit)


@router.get("/overdue", response_model=list[LoanResponse])
async def get_overdue_loans(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await loan_service.get_overdue_loans(db, skip=skip, limit=limit)


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(loan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await loan_service.get_loan(db, loan_id)


@router.patch("/{loan_id}/return", response_model=LoanResponse)
async def return_loan(loan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await loan_service.return_loan(db, loan_id)


@router.patch("/{loan_id}/extend", response_model=LoanResponse)
async def extend_loan(loan_id: uuid.UUID, data: LoanExtend, db: AsyncSession = Depends(get_db)):
    return await loan_service.extend_loan(db, loan_id, data)
