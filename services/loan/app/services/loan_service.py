import uuid
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import book_client, fine_client, member_client
from app.models.loan import Loan, LoanStatus
from app.schemas.loan import LoanCreate, LoanExtend

DEFAULT_LOAN_DURATION_DAYS = 14


async def create_loan(db: AsyncSession, data: LoanCreate) -> Loan:
    member = await member_client.get_member(data.member_id)
    if member.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Member is not active",
        )

    book = await book_client.get_book(data.book_id)
    if book.get("available_copies", 0) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book is not available",
        )

    today = date.today()
    loan = Loan(
        member_id=data.member_id,
        book_id=data.book_id,
        loan_date=today,
        due_date=today + timedelta(days=DEFAULT_LOAN_DURATION_DAYS),
        status=LoanStatus.active,
    )
    db.add(loan)

    await book_client.update_stock(data.book_id, -1)

    await db.commit()
    await db.refresh(loan)
    return loan


async def return_loan(db: AsyncSession, loan_id: uuid.UUID) -> Loan:
    loan = await get_loan(db, loan_id)

    if loan.status != LoanStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Loan is not active",
        )

    today = date.today()
    loan.return_date = today

    if today > loan.due_date:
        days_overdue = (today - loan.due_date).days
        amount = float(days_overdue * 1000)
        await fine_client.create_fine(loan.id, loan.member_id, amount)

    loan.status = LoanStatus.returned
    await book_client.update_stock(loan.book_id, 1)

    await db.commit()
    await db.refresh(loan)
    return loan


async def extend_loan(db: AsyncSession, loan_id: uuid.UUID, data: LoanExtend) -> Loan:
    loan = await get_loan(db, loan_id)

    if loan.status != LoanStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active loans can be extended",
        )

    loan.due_date = loan.due_date + timedelta(days=data.extra_days)
    await db.commit()
    await db.refresh(loan)
    return loan


async def list_loans(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[Loan]:
    result = await db.execute(
        select(Loan).order_by(Loan.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_loan(db: AsyncSession, loan_id: uuid.UUID) -> Loan:
    loan = await db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    return loan


async def get_overdue_loans(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[Loan]:
    today = date.today()
    result = await db.execute(
        select(Loan)
        .where(Loan.status == LoanStatus.active, Loan.due_date < today)
        .order_by(Loan.due_date)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_loans_by_member_id(db: AsyncSession, member_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[Loan]:
    result = await db.execute(
        select(Loan)
        .where(Loan.member_id == member_id)
        .order_by(Loan.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
