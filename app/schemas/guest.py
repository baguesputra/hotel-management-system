from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr


class GuestBase(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    address: str | None = None
    id_number: str | None = None


class GuestCreate(GuestBase):
    pass


class GuestUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    id_number: str | None = None


class GuestResponse(GuestBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}