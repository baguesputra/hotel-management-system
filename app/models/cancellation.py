import uuid
import enum
from sqlalchemy import Column, String, Numeric, Enum, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PROCESSED = "processed"
    REJECTED = "rejected"


class Cancellation(Base):
    __tablename__ = "cancellations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False, unique=True)
    reason = Column(Text, nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=False)
    refund_amount = Column(Numeric(12, 2), nullable=False, default=0)
    refund_percentage = Column(Numeric(5, 2), nullable=False, default=0)
    refund_status = Column(Enum(RefundStatus), default=RefundStatus.PENDING, nullable=False)
    refund_notes = Column(Text, nullable=True)

    # Relationships
    booking = relationship("Booking", back_populates="cancellation")

    def __repr__(self):
        return f"<Cancellation {self.booking_id} refund:{self.refund_amount}>"