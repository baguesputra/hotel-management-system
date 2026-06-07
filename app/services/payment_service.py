from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.payment import Payment, PaymentStatus
from app.models.booking import Booking, BookingStatus
from app.schemas.payment import PaymentCreate
from app.tasks.email_tasks import send_payment_receipt
from app.models.guest import Guest

class PaymentService:

    async def create(self, db: AsyncSession, data: PaymentCreate) -> Payment:
        # cek booking ada
        booking_result = await db.execute(
            select(Booking).where(Booking.id == data.booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking tidak ditemukan"
            )

        # cek payment sudah ada
        existing = await db.execute(
            select(Payment).where(Payment.booking_id == data.booking_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment untuk booking ini sudah ada"
            )

        payment = Payment(
            booking_id=data.booking_id,
            amount=booking.total_amount,
            payment_method=data.payment_method,
            notes=data.notes,
            status=PaymentStatus.PENDING,
        )
        db.add(payment)
        await db.flush()
        await db.refresh(payment)
        return payment

    async def get_by_id(self, db: AsyncSession, payment_id: UUID) -> Payment:
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment tidak ditemukan"
            )
        return payment

    async def confirm(self, db: AsyncSession, payment_id: UUID) -> Payment:
        payment = await self.get_by_id(db, payment_id)
        if payment.status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment sudah diproses sebelumnya"
            )
        payment.status = PaymentStatus.PAID

        # update booking jadi confirmed
        booking_result = await db.execute(
            select(Booking).where(Booking.id == payment.booking_id)
        )
        booking = booking_result.scalar_one()
        booking.status = BookingStatus.CONFIRMED

        await db.flush()
        await db.refresh(payment)
        guest_result = await db.execute(
        select(Guest).where(Guest.id == booking.guest_id)
        )
        guest = guest_result.scalar_one()

        send_payment_receipt.delay({
            "guest_name": guest.name,
            "guest_email": guest.email,
            "booking_code": booking.booking_code,
            "payment_method": payment.payment_method.value,
            "amount": float(payment.amount),
        })
        return payment


payment_service = PaymentService()