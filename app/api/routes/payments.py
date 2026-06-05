from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=PaymentResponse, status_code=201)
async def create_payment(data: PaymentCreate, db: AsyncSession = Depends(get_db)):
    return await payment_service.create(db, data)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: UUID, db: AsyncSession = Depends(get_db)):
    return await payment_service.get_by_id(db, payment_id)


@router.patch("/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(payment_id: UUID, db: AsyncSession = Depends(get_db)):
    return await payment_service.confirm(db, payment_id)