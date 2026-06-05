from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from app.models.cancellation import RefundStatus


class CancellationCreate(BaseModel):
    booking_id: UUID
    reason: str | None = None


class CancellationResponse(BaseModel):
    id: UUID
    booking_id: UUID
    reason: str | None
    cancelled_at: datetime
    refund_amount: Decimal
    refund_percentage: Decimal
    refund_status: RefundStatus
    refund_notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}