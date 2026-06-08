from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import booking_service
import os
from fastapi.responses import FileResponse
from celery.result import AsyncResult
from app.celery_app import celery_app
from app.tasks.report_tasks import generate_invoice

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

@router.get("/{booking_id}/invoice")
async def download_invoice(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Download invoice PDF untuk booking yang sudah check-out."""
    booking = await booking_service.get_by_id(db, booking_id)

    # cari file invoice yang sudah digenerate
    reports_dir = "reports"
    invoice_files = [
        f for f in os.listdir(reports_dir)
        if f.startswith(f"invoice_{booking.booking_code}_")
    ] if os.path.exists(reports_dir) else []

    if not invoice_files:
        # generate on-demand kalau belum ada
        task = generate_invoice.delay(str(booking_id))
        return {
            "message": "Invoice sedang digenerate",
            "task_id": task.id
        }

    # ambil yang terbaru
    latest_invoice = sorted(invoice_files)[-1]
    filepath = os.path.join(reports_dir, latest_invoice)

    return FileResponse(
        path=filepath,
        media_type="application/pdf",
        filename=latest_invoice,
    )