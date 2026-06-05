from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.waitlist import Waitlist, WaitlistStatus
from app.schemas.waitlist import WaitlistCreate


class WaitlistService:

    async def join(self, db: AsyncSession, data: WaitlistCreate) -> Waitlist:
        # cek sudah ada di waitlist untuk room & tanggal yang sama
        existing = await db.execute(
            select(Waitlist).where(
                Waitlist.guest_id == data.guest_id,
                Waitlist.room_id == data.room_id,
                Waitlist.check_in_date == data.check_in_date,
                Waitlist.status == WaitlistStatus.WAITING,
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
        entry = await self.get_by_id(db, waitlist_id)
        result = await db.execute(
            select(func.count()).where(
                Waitlist.room_id == entry.room_id,
                Waitlist.check_in_date == entry.check_in_date,
                Waitlist.status == WaitlistStatus.WAITING,
                Waitlist.created_at <= entry.created_at,
            )
        )
        return result.scalar()

    async def cancel(self, db: AsyncSession, waitlist_id: UUID) -> None:
        entry = await self.get_by_id(db, waitlist_id)
        if entry.status != WaitlistStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hanya entry dengan status WAITING yang bisa dibatalkan"
            )
        entry.status = WaitlistStatus.CANCELLED
        await db.flush()


waitlist_service = WaitlistService()