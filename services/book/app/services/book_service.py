import uuid

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate, StockUpdate


async def list_books(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[Book]:
    result = await db.execute(select(Book).order_by(Book.title).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_book(db: AsyncSession, book_id: uuid.UUID) -> Book:
    book = await db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


async def search_books(db: AsyncSession, query: str, skip: int = 0, limit: int = 20) -> list[Book]:
    pattern = f"%{query}%"
    stmt = (
        select(Book)
        .where(or_(Book.title.ilike(pattern), Book.author.ilike(pattern), Book.category.ilike(pattern)))
        .order_by(Book.title)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _assert_isbn_available(db: AsyncSession, isbn: str, exclude_id: uuid.UUID | None = None) -> None:
    stmt = select(Book).where(Book.isbn == isbn)
    if exclude_id is not None:
        stmt = stmt.where(Book.id != exclude_id)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ISBN already exists")


async def create_book(db: AsyncSession, data: BookCreate) -> Book:
    await _assert_isbn_available(db, data.isbn)

    book = Book(**data.model_dump(), available_copies=data.total_copies)
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book


async def update_book(db: AsyncSession, book_id: uuid.UUID, data: BookUpdate) -> Book:
    book = await get_book(db, book_id)
    changes = data.model_dump(exclude_unset=True)

    if "isbn" in changes and changes["isbn"] != book.isbn:
        await _assert_isbn_available(db, changes["isbn"], exclude_id=book.id)

    if "total_copies" in changes:
        new_total = changes["total_copies"]
        borrowed = book.total_copies - book.available_copies
        if new_total < borrowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot set total copies below the number currently on loan",
            )
        book.available_copies = new_total - borrowed

    for field, value in changes.items():
        setattr(book, field, value)

    await db.commit()
    await db.refresh(book)
    return book


async def delete_book(db: AsyncSession, book_id: uuid.UUID) -> None:
    book = await get_book(db, book_id)
    await db.delete(book)
    await db.commit()


async def update_stock(db: AsyncSession, book_id: uuid.UUID, data: StockUpdate) -> Book:
    # Row-level lock guards concurrent borrow/return requests touching the same book.
    stmt = select(Book).where(Book.id == book_id).with_for_update()
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    new_available = book.available_copies + data.delta
    if new_available < 0 or new_available > book.total_copies:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Resulting available stock would be out of valid range",
        )

    book.available_copies = new_available
    await db.commit()
    await db.refresh(book)
    return book
