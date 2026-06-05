from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import booking_service

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(data: BookingCreate, db: AsyncSession = Depends(get_db)):
    return await booking_service.create(db, data)


@router.get("", response_model=list[BookingResponse])
async def list_bookings(db: AsyncSession = Depends(get_db)):
    return await booking_service.get_all(db)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: UUID, db: AsyncSession = Depends(get_db)):
    return await booking_service.get_by_id(db, booking_id)


@router.patch("/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(booking_id: UUID, db: AsyncSession = Depends(get_db)):
    return await booking_service.confirm(db, booking_id)


@router.patch("/{booking_id}/check-in", response_model=BookingResponse)
async def check_in(booking_id: UUID, db: AsyncSession = Depends(get_db)):
    return await booking_service.check_in(db, booking_id)


@router.patch("/{booking_id}/check-out", response_model=BookingResponse)
async def check_out(booking_id: UUID, db: AsyncSession = Depends(get_db)):
    return await booking_service.check_out(db, booking_id)