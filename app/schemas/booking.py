from uuid import UUID
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, model_validator
from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    guest_id: UUID
    room_id: UUID
    check_in_date: date
    check_out_date: date
    num_guests: int = 1
    special_requests: str | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.check_out_date <= self.check_in_date:
            raise ValueError("check_out_date harus setelah check_in_date")
        return self


class BookingResponse(BaseModel):
    id: UUID
    booking_code: str
    guest_id: UUID
    room_id: UUID
    check_in_date: date
    check_out_date: date
    num_guests: int
    total_nights: int
    price_per_night: Decimal
    total_amount: Decimal
    status: BookingStatus
    special_requests: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}