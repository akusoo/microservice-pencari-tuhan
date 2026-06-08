import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.loan import LoanStatus


class LoanCreate(BaseModel):
    member_id: uuid.UUID
    book_id: uuid.UUID


class LoanExtend(BaseModel):
    extra_days: int = Field(..., ge=1, le=14)


class LoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    member_id: uuid.UUID
    book_id: uuid.UUID
    loan_date: date
    due_date: date
    return_date: date | None
    status: LoanStatus
    created_at: datetime
    updated_at: datetime
