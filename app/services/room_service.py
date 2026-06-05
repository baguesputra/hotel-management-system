from uuid import UUID
from datetime import date
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.room import Room, RoomPricing, RoomStatus, RoomType
from app.models.booking import Booking, BookingStatus
from app.schemas.room import RoomCreate, RoomUpdate, RoomPricingCreate


class RoomService:

    async def create(self, db: AsyncSession, data: RoomCreate) -> Room:
        existing = await db.execute(
            select(Room).where(Room.room_number == data.room_number)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nomor kamar sudah ada"
            )
        room = Room(**data.model_dump())
        db.add(room)
        await db.flush()
        await db.refresh(room)
        return room

    async def get_all(self, db: AsyncSession, room_type: RoomType | None = None) -> list[Room]:
        query = select(Room).where(Room.is_active == True)
        if room_type:
            query = query.where(Room.room_type == room_type)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, room_id: UUID) -> Room:
        result = await db.execute(
            select(Room).where(Room.id == room_id, Room.is_active == True)
        )
        room = result.scalar_one_or_none()
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kamar tidak ditemukan"
            )
        return room

    async def update(self, db: AsyncSession, room_id: UUID, data: RoomUpdate) -> Room:
        room = await self.get_by_id(db, room_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(room, field, value)
        await db.flush()
        await db.refresh(room)
        return room

    async def get_available_rooms(
        self,
        db: AsyncSession,
        check_in: date,
        check_out: date,
        room_type: RoomType | None = None
    ) -> list[Room]:
        # ambil room_id yang sudah dibooking di tanggal tersebut
        booked_subquery = select(Booking.room_id).where(
            and_(
                Booking.status.in_([
                    BookingStatus.CONFIRMED,
                    BookingStatus.CHECKED_IN,
                    BookingStatus.PENDING,
                ]),
                or_(
                    and_(
                        Booking.check_in_date <= check_in,
                        Booking.check_out_date > check_in,
                    ),
                    and_(
                        Booking.check_in_date < check_out,
                        Booking.check_out_date >= check_out,
                    ),
                    and_(
                        Booking.check_in_date >= check_in,
                        Booking.check_out_date <= check_out,
                    ),
                )
            )
        )

        query = select(Room).where(
            and_(
                Room.is_active == True,
                Room.status == RoomStatus.AVAILABLE,
                Room.id.not_in(booked_subquery),
            )
        )

        if room_type:
            query = query.where(Room.room_type == room_type)

        result = await db.execute(query)
        return result.scalars().all()

    async def add_pricing(
        self,
        db: AsyncSession,
        room_id: UUID,
        data: RoomPricingCreate
    ) -> RoomPricing:
        await self.get_by_id(db, room_id)
        pricing = RoomPricing(room_id=room_id, **data.model_dump())
        db.add(pricing)
        await db.flush()
        await db.refresh(pricing)
        return pricing


room_service = RoomService()