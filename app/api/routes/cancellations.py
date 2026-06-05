from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.cancellation import CancellationCreate, CancellationResponse
from app.services.cancellation_service import cancellation_service

router = APIRouter(prefix="/cancellations", tags=["Cancellations"])


@router.post("", response_model=CancellationResponse, status_code=201)
async def cancel_booking(data: CancellationCreate, db: AsyncSession = Depends(get_db)):
    return await cancellation_service.create(db, data)


@router.get("/{cancellation_id}", response_model=CancellationResponse)
async def get_cancellation(cancellation_id: UUID, db: AsyncSession = Depends(get_db)):
    return await cancellation_service.get_by_id(db, cancellation_id)


@router.patch("/{cancellation_id}/approve", response_model=CancellationResponse)
async def approve_refund(cancellation_id: UUID, db: AsyncSession = Depends(get_db)):
    return await cancellation_service.approve_refund(db, cancellation_id)