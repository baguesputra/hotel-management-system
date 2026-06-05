from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.models.payment import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    booking_id: UUID
    payment_method: PaymentMethod
    notes: str | None = None


class PaymentResponse(BaseModel):
    id: UUID
    booking_id: UUID
    amount: Decimal
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_id: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}