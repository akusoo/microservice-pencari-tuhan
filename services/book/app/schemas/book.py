import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: str = Field(..., min_length=10, max_length=20)
    publisher: str | None = Field(None, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    year: int | None = Field(None, ge=0)


class BookCreate(BookBase):
    total_copies: int = Field(..., ge=1)


class BookUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    author: str | None = Field(None, min_length=1, max_length=255)
    isbn: str | None = Field(None, min_length=10, max_length=20)
    publisher: str | None = Field(None, max_length=255)
    category: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    year: int | None = Field(None, ge=0)
    total_copies: int | None = Field(None, ge=1)


class BookResponse(BookBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    total_copies: int
    available_copies: int
    created_at: datetime
    updated_at: datetime


class StockUpdate(BaseModel):
    delta: int = Field(
        ...,
        description="Stock change to apply: negative when a loan is taken out, positive on return/restock",
    )
