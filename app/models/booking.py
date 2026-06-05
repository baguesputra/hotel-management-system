import uuid
import enum
from sqlalchemy import Column, String, Date, Integer, Numeric, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_code = Column(String(20), unique=True, nullable=False, index=True)
    guest_id = Column(UUID(as_uuid=True), ForeignKey("guests.id"), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    num_guests = Column(Integer, nullable=False, default=1)
    total_nights = Column(Integer, nullable=False)
    price_per_night = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    special_requests = Column(Text, nullable=True)

    # Relationships
    guest = relationship("Guest", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False)
    cancellation = relationship("Cancellation", back_populates="booking", uselist=False)

    def __repr__(self):
        return f"<Booking {self.booking_code} ({self.status})>"