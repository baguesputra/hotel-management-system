import uuid
import enum
from sqlalchemy import Column, String, Enum, ForeignKey, Date, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class WaitlistStatus(str, enum.Enum):
    WAITING = "waiting"
    NOTIFIED = "notified"
    BOOKED = "booked"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Waitlist(Base):
    __tablename__ = "waitlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guest_id = Column(UUID(as_uuid=True), ForeignKey("guests.id"), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    status = Column(Enum(WaitlistStatus), default=WaitlistStatus.WAITING, nullable=False)
    notified_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 24 jam setelah notified
    notes = Column(Text, nullable=True)

    # Relationships
    guest = relationship("Guest", back_populates="waitlist_entries")
    room = relationship("Room", back_populates="waitlist_entries")

    def __repr__(self):
        return f"<Waitlist {self.guest_id} room:{self.room_id} ({self.status})>"