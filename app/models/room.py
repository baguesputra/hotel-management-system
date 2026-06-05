import uuid
import enum
from sqlalchemy import Column, String, Integer, Numeric, Text, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class RoomType(str, enum.Enum):
    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"
    PRESIDENTIAL = "presidential"


class RoomStatus(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    CLEANING = "cleaning"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_number = Column(String(10), unique=True, nullable=False, index=True)
    room_type = Column(Enum(RoomType), nullable=False)
    floor = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False, default=2)
    base_price = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(RoomStatus), default=RoomStatus.AVAILABLE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    bookings = relationship("Booking", back_populates="room")
    pricings = relationship("RoomPricing", back_populates="room")
    waitlist_entries = relationship("Waitlist", back_populates="room")

    def __repr__(self):
        return f"<Room {self.room_number} ({self.room_type})>"


class SeasonType(str, enum.Enum):
    REGULAR = "regular"
    PEAK = "peak"
    HOLIDAY = "holiday"


class RoomPricing(Base):
    __tablename__ = "room_pricings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    season_type = Column(Enum(SeasonType), nullable=False)
    price_multiplier = Column(Numeric(4, 2), nullable=False, default=1.0)
    start_date = Column(String(10), nullable=False)  # format: MM-DD
    end_date = Column(String(10), nullable=False)    # format: MM-DD

    # Relationships
    room = relationship("Room", back_populates="pricings")

    def __repr__(self):
        return f"<RoomPricing {self.room_id} {self.season_type}>"