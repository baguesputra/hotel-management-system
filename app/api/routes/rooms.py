from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.db.session import get_db
from app.schemas.room import (
    RoomCreate, RoomUpdate, RoomResponse,
    RoomPricingCreate, RoomPricingResponse
)
from app.models.room import RoomType
from app.services.room_service import room_service

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post("", response_model=RoomResponse, status_code=201)
async def create_room(data: RoomCreate, db: AsyncSession = Depends(get_db)):
    return await room_service.create(db, data)


@router.get("", response_model=list[RoomResponse])
async def list_rooms(
    room_type: RoomType | None = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    return await room_service.get_all(db, room_type)


@router.get("/availability", response_model=list[RoomResponse])
async def check_availability(
    check_in_date: date = Query(...),
    check_out_date: date = Query(...),
    room_type: RoomType | None = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    return await room_service.get_available_rooms(db, check_in_date, check_out_date, room_type)


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: UUID, db: AsyncSession = Depends(get_db)):
    return await room_service.get_by_id(db, room_id)


@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(room_id: UUID, data: RoomUpdate, db: AsyncSession = Depends(get_db)):
    return await room_service.update(db, room_id, data)


@router.post("/{room_id}/pricing", response_model=RoomPricingResponse, status_code=201)
async def add_room_pricing(
    room_id: UUID,
    data: RoomPricingCreate,
    db: AsyncSession = Depends(get_db)
):
    return await room_service.add_pricing(db, room_id, data)