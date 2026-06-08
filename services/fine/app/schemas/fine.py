import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FineCreate(BaseModel):
    loan_id: uuid.UUID
    member_id: uuid.UUID
    amount: float = Field(..., gt=0)


class FineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    loan_id: uuid.UUID
    member_id: uuid.UUID
    amount: float
    is_paid: bool
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime
