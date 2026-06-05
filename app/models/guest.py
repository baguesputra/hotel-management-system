import uuid
from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Guest(Base):
    __tablename__ = "guests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    id_number = Column(String(50), nullable=True)  # KTP/Passport
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    bookings = relationship("Booking", back_populates="guest")
    waitlist_entries = relationship("Waitlist", back_populates="guest")

    def __repr__(self):
        return f"<Guest {self.name} ({self.email})>"