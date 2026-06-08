from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, model_validator
from app.models.waitlist import WaitlistStatus


class WaitlistCreate(BaseModel):
    guest_id: UUID
    room_id: UUID
    check_in_date: date
    check_out_date: date
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.check_out_date <= self.check_in_date:
            raise ValueError("check_out_date harus setelah check_in_date")
        return self


class WaitlistResponse(BaseModel):
    id: UUID
    guest_id: UUID
    room_id: UUID
    check_in_date: date
    check_out_date: date
    status: WaitlistStatus
    notified_at: datetime | None
    expires_at: datetime | None
    notes: str | None
    position: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WaitlistListResponse(BaseModel):
    """Response untuk list waitlist per room."""
    id: UUID
    guest_id: UUID
    room_id: UUID
    check_in_date: date
    check_out_date: date
    status: WaitlistStatus
    position: int
    created_at: datetime

    model_config = {"from_attributes": True}


class WaitlistTriggerRequest(BaseModel):
    """Request untuk manual trigger notifikasi."""
    room_id: UUID
    check_in_date: date
    check_out_date: date