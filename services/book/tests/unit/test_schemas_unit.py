# Unit tests: Pydantic schema validation in isolation — no app, no DB, no HTTP.
# Pins the request-shape rules the API relies on before anything reaches the DB.

import pytest
from pydantic import ValidationError

from app.schemas.book import BookCreate, BookUpdate, StockUpdate


def base_payload(**overrides):
    payload = {
        "title": "Sapiens",
        "author": "Yuval Noah Harari",
        "isbn": "9780062316097",
        "category": "history",
        "total_copies": 3,
    }
    payload.update(overrides)
    return payload


def test_book_create_accepts_valid_payload():
    book = BookCreate(**base_payload())
    assert book.total_copies == 3
    assert book.publisher is None  # optional field defaults to None


def test_book_create_rejects_total_copies_below_one():
    with pytest.raises(ValidationError, match="total_copies"):
        BookCreate(**base_payload(total_copies=0))


def test_book_create_rejects_isbn_shorter_than_ten_chars():
    with pytest.raises(ValidationError, match="isbn"):
        BookCreate(**base_payload(isbn="123"))


def test_book_create_rejects_negative_year():
    with pytest.raises(ValidationError, match="year"):
        BookCreate(**base_payload(year=-1))


def test_book_update_allows_all_fields_omitted():
    # PUT supports partial updates — an empty body must be valid.
    update = BookUpdate()
    assert update.model_dump(exclude_unset=True) == {}


def test_stock_update_requires_integer_delta():
    assert StockUpdate(delta=-1).delta == -1

    with pytest.raises(ValidationError, match="delta"):
        StockUpdate(**{})

    with pytest.raises(ValidationError):
        StockUpdate(delta="not-a-number")
