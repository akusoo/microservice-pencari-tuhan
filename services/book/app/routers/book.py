import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_auth_context, require_roles
from app.db.session import get_db
from app.schemas.book import BookCreate, BookResponse, BookUpdate, StockUpdate
from app.services import book_service

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookResponse])
async def list_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.list_books(db, skip=skip, limit=limit)


@router.get("/search", response_model=list[BookResponse])
async def search_books(
    q: str = Query(..., min_length=1, description="Search by title, author, or category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.search_books(db, query=q, skip=skip, limit=limit)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await book_service.get_book(db, book_id)


@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "librarian"))],
)
async def create_book(data: BookCreate, db: AsyncSession = Depends(get_db)):
    return await book_service.create_book(db, data)


@router.put(
    "/{book_id}",
    response_model=BookResponse,
    dependencies=[Depends(require_roles("admin", "librarian"))],
)
async def update_book(book_id: uuid.UUID, data: BookUpdate, db: AsyncSession = Depends(get_db)):
    return await book_service.update_book(db, book_id, data)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
)
async def delete_book(book_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await book_service.delete_book(db, book_id)


@router.patch(
    "/{book_id}/stock",
    response_model=BookResponse,
    dependencies=[Depends(get_auth_context)],
)
async def update_stock(book_id: uuid.UUID, data: StockUpdate, db: AsyncSession = Depends(get_db)):
    return await book_service.update_stock(db, book_id, data)
