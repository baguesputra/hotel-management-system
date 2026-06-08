from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.waitlist import Waitlist, WaitlistStatus
from app.models.booking import Booking, BookingStatus
from app.schemas.waitlist import WaitlistCreate


class WaitlistService:

    async def _is_room_available(
        self,
        db: AsyncSession,
        room_id: UUID,
        check_in_date,
        check_out_date,
    ) -> bool:
        """Cek apakah kamar benar-benar tidak tersedia di tanggal tersebut."""
        from sqlalchemy import or_
        result = await db.execute(
            select(Booking).where(
                and_(
                    Booking.room_id == room_id,
                    Booking.status.in_([
                        BookingStatus.PENDING,
                        BookingStatus.CONFIRMED,
                        BookingStatus.CHECKED_IN,
                    ]),
                    or_(
                        and_(
                            Booking.check_in_date <= check_in_date,
                            Booking.check_out_date > check_in_date,
                        ),
                        and_(
                            Booking.check_in_date < check_out_date,
                            Booking.check_out_date >= check_out_date,
                        ),
                        and_(
                            Booking.check_in_date >= check_in_date,
                            Booking.check_out_date <= check_out_date,
                        ),
                    )
                )
            )
        )
        booking = result.scalar_one_or_none()
        return booking is None  # True = tersedia, False = tidak tersedia

    async def join(self, db: AsyncSession, data: WaitlistCreate) -> Waitlist:
        # validasi: kamar harus tidak tersedia dulu
        # tidak masuk akal join waitlist kalau kamar masih kosong
        is_available = await self._is_room_available(
            db, data.room_id, data.check_in_date, data.check_out_date
        )
        if is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kamar masih tersedia, silakan langsung booking"
            )

        # cek sudah ada di waitlist untuk room & tanggal yang sama
        existing = await db.execute(
            select(Waitlist).where(
                and_(
                    Waitlist.guest_id == data.guest_id,
                    Waitlist.room_id == data.room_id,
                    Waitlist.check_in_date == data.check_in_date,
                    Waitlist.status == WaitlistStatus.WAITING,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guest sudah ada di waitlist untuk kamar dan tanggal ini"
            )

        entry = Waitlist(**data.model_dump())
        db.add(entry)
        await db.flush()
        await db.refresh(entry)
        return entry

    async def get_by_id(self, db: AsyncSession, waitlist_id: UUID) -> Waitlist:
        result = await db.execute(
            select(Waitlist).where(Waitlist.id == waitlist_id)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Waitlist entry tidak ditemukan"
            )
        return entry

    async def get_position(self, db: AsyncSession, waitlist_id: UUID) -> int:
        """Hitung posisi antrian — berdasarkan waktu join (created_at)."""
        entry = await self.get_by_id(db, waitlist_id)
        result = await db.execute(
            select(func.count()).where(
                and_(
                    Waitlist.room_id == entry.room_id,
                    Waitlist.check_in_date == entry.check_in_date,
                    Waitlist.status == WaitlistStatus.WAITING,
                    Waitlist.created_at <= entry.created_at,
                )
            )
        )
        return result.scalar()

    async def get_by_room(
        self,
        db: AsyncSession,
        room_id: UUID,
        check_in_date=None,
    ) -> list[Waitlist]:
        """Ambil semua waitlist entry untuk room tertentu."""
        query = select(Waitlist).where(
            and_(
                Waitlist.room_id == room_id,
                Waitlist.status == WaitlistStatus.WAITING,
            )
        ).order_by(Waitlist.created_at)

        if check_in_date:
            query = query.where(Waitlist.check_in_date == check_in_date)

        result = await db.execute(query)
        return result.scalars().all()

    async def cancel(self, db: AsyncSession, waitlist_id: UUID) -> None:
        entry = await self.get_by_id(db, waitlist_id)
        if entry.status not in [WaitlistStatus.WAITING, WaitlistStatus.NOTIFIED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Entry ini tidak bisa dibatalkan"
            )
        entry.status = WaitlistStatus.CANCELLED
        await db.flush()

    async def trigger_notification(
        self,
        db: AsyncSession,
        room_id: UUID,
        check_in_date: str,
        check_out_date: str,
    ) -> dict:
        """Manual trigger notifikasi waitlist oleh staff."""
        from app.tasks.waitlist_tasks import notify_waitlist_on_cancellation
        task = notify_waitlist_on_cancellation.delay(
            str(room_id), check_in_date, check_out_date
        )
        return {
            "message": "Notifikasi waitlist sedang diproses",
            "task_id": task.id,
        }


waitlist_service = WaitlistService()