import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.member import MemberStatus


class MemberBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(None, max_length=30)
    address: str | None = Field(None, max_length=255)


class MemberCreate(MemberBase):
    user_id: uuid.UUID


class MemberUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=30)
    address: str | None = Field(None, max_length=255)


class MemberStatusUpdate(BaseModel):
    status: MemberStatus


class MemberResponse(MemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    status: MemberStatus
    created_at: datetime
    updated_at: datetime
