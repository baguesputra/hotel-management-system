from uuid import UUID
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel
from app.models.room import RoomType, RoomStatus, SeasonType

class RoomBase(BaseModel):
    room_number: str
    room_type: RoomType
    floor: int
    capacity: int = 2
    base_price: Decimal
    description: str | None = None


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    room_type: RoomType | None = None
    floor: int | None = None
    capacity: int | None = None
    base_price: Decimal | None = None
    description: str | None = None
    status: RoomStatus | None = None


class RoomResponse(RoomBase):
    id: UUID
    status: RoomStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoomPricingCreate(BaseModel):
    season_type: SeasonType
    price_multiplier: Decimal
    start_date: str  # format: MM-DD
    end_date: str    # format: MM-DD


class RoomPricingResponse(RoomPricingCreate):
    id: UUID
    room_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class RoomAvailabilityQuery(BaseModel):
    check_in_date: str   # format: YYYY-MM-DD
    check_out_date: str  # format: YYYY-MM-DD
    room_type: RoomType | None = None

class PriceEstimationResponse(BaseModel):
    room_id: UUID
    room_number: str
    room_type: RoomType
    check_in_date: date
    check_out_date: date
    total_nights: int
    price_per_night: Decimal
    total_amount: Decimal