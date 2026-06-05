import random
import string
from uuid import UUID
from datetime import date
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.booking import Booking, BookingStatus
from app.models.room import Room, RoomStatus
from app.schemas.booking import BookingCreate
from app.services.room_service import room_service


class BookingService:

    def _generate_booking_code(self) -> str:
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"HTL-{suffix}"

    async def create(self, db: AsyncSession, data: BookingCreate) -> Booking:
        # cek availability
        available_rooms = await room_service.get_available_rooms(
            db, data.check_in_date, data.check_out_date
        )
        available_ids = [r.id for r in available_rooms]

        if data.room_id not in available_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kamar tidak tersedia di tanggal tersebut"
            )

        # ambil data room untuk hitung harga
        room = await room_service.get_by_id(db, data.room_id)
        total_nights = (data.check_out_date - data.check_in_date).days
        price_per_night = Decimal(str(room.base_price))
        total_amount = price_per_night * total_nights

        booking = Booking(
            booking_code=self._generate_booking_code(),
            guest_id=data.guest_id,
            room_id=data.room_id,
            check_in_date=data.check_in_date,
            check_out_date=data.check_out_date,
            num_guests=data.num_guests,
            total_nights=total_nights,
            price_per_night=price_per_night,
            total_amount=total_amount,
            special_requests=data.special_requests,
            status=BookingStatus.PENDING,
        )
        db.add(booking)
        await db.flush()
        await db.refresh(booking)
        return booking

    async def get_all(self, db: AsyncSession) -> list[Booking]:
        result = await db.execute(select(Booking))
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, booking_id: UUID) -> Booking:
        result = await db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking tidak ditemukan"
            )
        return booking

    async def confirm(self, db: AsyncSession, booking_id: UUID) -> Booking:
        booking = await self.get_by_id(db, booking_id)
        if booking.status != BookingStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Booking tidak bisa dikonfirmasi, status saat ini: {booking.status}"
            )
        booking.status = BookingStatus.CONFIRMED
        await db.flush()
        await db.refresh(booking)
        return booking

    async def check_in(self, db: AsyncSession, booking_id: UUID) -> Booking:
        booking = await self.get_by_id(db, booking_id)
        if booking.status != BookingStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking harus berstatus CONFIRMED untuk check-in"
            )
        booking.status = BookingStatus.CHECKED_IN

        # update status kamar jadi occupied
        result = await db.execute(select(Room).where(Room.id == booking.room_id))
        room = result.scalar_one()
        room.status = RoomStatus.OCCUPIED

        await db.flush()
        await db.refresh(booking)
        return booking

    async def check_out(self, db: AsyncSession, booking_id: UUID) -> Booking:
        booking = await self.get_by_id(db, booking_id)
        if booking.status != BookingStatus.CHECKED_IN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking harus berstatus CHECKED_IN untuk check-out"
            )
        booking.status = BookingStatus.CHECKED_OUT

        # update status kamar jadi available
        result = await db.execute(select(Room).where(Room.id == booking.room_id))
        room = result.scalar_one()
        room.status = RoomStatus.AVAILABLE

        await db.flush()
        await db.refresh(booking)
        return booking


booking_service = BookingService()