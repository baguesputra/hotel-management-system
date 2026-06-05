from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.guest import Guest
from app.schemas.guest import GuestCreate, GuestUpdate


class GuestService:

    async def create(self, db: AsyncSession, data: GuestCreate) -> Guest:
        # cek email sudah terdaftar
        existing = await db.execute(
            select(Guest).where(Guest.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email sudah terdaftar"
            )

        guest = Guest(**data.model_dump())
        db.add(guest)
        await db.flush()
        await db.refresh(guest)
        return guest

    async def get_all(self, db: AsyncSession) -> list[Guest]:
        result = await db.execute(
            select(Guest).where(Guest.is_active == True)
        )
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, guest_id: UUID) -> Guest:
        result = await db.execute(
            select(Guest).where(Guest.id == guest_id, Guest.is_active == True)
        )
        guest = result.scalar_one_or_none()
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest tidak ditemukan"
            )
        return guest

    async def update(self, db: AsyncSession, guest_id: UUID, data: GuestUpdate) -> Guest:
        guest = await self.get_by_id(db, guest_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(guest, field, value)
        await db.flush()
        await db.refresh(guest)
        return guest

    async def delete(self, db: AsyncSession, guest_id: UUID) -> None:
        guest = await self.get_by_id(db, guest_id)
        guest.is_active = False
        await db.flush()


guest_service = GuestService()