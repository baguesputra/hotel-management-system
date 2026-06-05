from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.guest import GuestCreate, GuestUpdate, GuestResponse
from app.services.guest_service import guest_service

router = APIRouter(prefix="/guests", tags=["Guests"])


@router.post("", response_model=GuestResponse, status_code=201)
async def create_guest(data: GuestCreate, db: AsyncSession = Depends(get_db)):
    return await guest_service.create(db, data)


@router.get("", response_model=list[GuestResponse])
async def list_guests(db: AsyncSession = Depends(get_db)):
    return await guest_service.get_all(db)


@router.get("/{guest_id}", response_model=GuestResponse)
async def get_guest(guest_id: UUID, db: AsyncSession = Depends(get_db)):
    return await guest_service.get_by_id(db, guest_id)


@router.put("/{guest_id}", response_model=GuestResponse)
async def update_guest(guest_id: UUID, data: GuestUpdate, db: AsyncSession = Depends(get_db)):
    return await guest_service.update(db, guest_id, data)


@router.delete("/{guest_id}", status_code=204)
async def delete_guest(guest_id: UUID, db: AsyncSession = Depends(get_db)):
    await guest_service.delete(db, guest_id)