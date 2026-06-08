from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.waitlist import (
    WaitlistCreate,
    WaitlistResponse,
    WaitlistListResponse,
    WaitlistTriggerRequest,
)
from app.services.waitlist_service import waitlist_service

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post("", response_model=WaitlistResponse, status_code=201)
async def join_waitlist(data: WaitlistCreate, db: AsyncSession = Depends(get_db)):
    """Join waitlist untuk kamar yang tidak tersedia."""
    entry = await waitlist_service.join(db, data)
    position = await waitlist_service.get_position(db, entry.id)
    response = WaitlistResponse.model_validate(entry)
    response.position = position
    return response


@router.get("/room/{room_id}", response_model=list[WaitlistListResponse])
async def get_waitlist_by_room(
    room_id: UUID,
    check_in_date: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Lihat semua guest yang antri untuk kamar tertentu."""
    entries = await waitlist_service.get_by_room(db, room_id, check_in_date)

    responses = []
    for idx, entry in enumerate(entries, start=1):
        response = WaitlistListResponse.model_validate(entry)
        response.position = idx
        responses.append(response)

    return responses


@router.get("/{waitlist_id}", response_model=WaitlistResponse)
async def get_waitlist_entry(
    waitlist_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Cek status dan posisi antrian."""
    entry = await waitlist_service.get_by_id(db, waitlist_id)
    position = await waitlist_service.get_position(db, waitlist_id)
    response = WaitlistResponse.model_validate(entry)
    response.position = position
    return response


@router.delete("/{waitlist_id}", status_code=204)
async def cancel_waitlist(
    waitlist_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Batalkan dari waitlist."""
    await waitlist_service.cancel(db, waitlist_id)


@router.post("/trigger-notification", status_code=202)
async def trigger_waitlist_notification(
    data: WaitlistTriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Manual trigger notifikasi ke semua guest di waitlist.
    Dipakai staff ketika ada kamar yang tiba-tiba tersedia.
    """
    result = await waitlist_service.trigger_notification(
        db,
        data.room_id,
        str(data.check_in_date),
        str(data.check_out_date),
    )
    return result