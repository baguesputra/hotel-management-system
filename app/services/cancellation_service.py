from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from celery import chain
from app.models.cancellation import Cancellation, RefundStatus
from app.models.booking import Booking, BookingStatus
from app.models.guest import Guest
from app.schemas.cancellation import CancellationCreate
from app.tasks.email_tasks import send_refund_confirmation
from app.tasks.refund_tasks import process_refund
from app.tasks.waitlist_tasks import notify_waitlist_on_cancellation


class CancellationService:

    def _calculate_refund(self, check_in_date, cancelled_at: datetime) -> tuple[Decimal, Decimal]:
        today = cancelled_at.date()
        days_before = (check_in_date - today).days

        if days_before >= 7:
            return Decimal("100.00"), Decimal("100.00")
        elif days_before >= 3:
            return Decimal("75.00"), Decimal("75.00")
        elif days_before >= 1:
            return Decimal("50.00"), Decimal("50.00")
        else:
            return Decimal("0.00"), Decimal("0.00")

    async def create(self, db: AsyncSession, data: CancellationCreate) -> Cancellation:
        booking_result = await db.execute(
            select(Booking).where(Booking.id == data.booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking tidak ditemukan"
            )

        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Booking tidak bisa dibatalkan, status: {booking.status}"
            )

        existing = await db.execute(
            select(Cancellation).where(Cancellation.booking_id == data.booking_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking ini sudah pernah dibatalkan"
            )

        cancelled_at = datetime.now(timezone.utc)
        refund_percentage, _ = self._calculate_refund(booking.check_in_date, cancelled_at)
        refund_amount = booking.total_amount * refund_percentage / 100

        cancellation = Cancellation(
            booking_id=data.booking_id,
            reason=data.reason,
            cancelled_at=cancelled_at,
            refund_amount=refund_amount,
            refund_percentage=refund_percentage,
            refund_status=RefundStatus.PENDING,
        )
        db.add(cancellation)
        booking.status = BookingStatus.CANCELLED
        await db.flush()

        guest_result = await db.execute(
            select(Guest).where(Guest.id == booking.guest_id)
        )
        guest = guest_result.scalar_one()

        send_refund_confirmation.delay({
            "guest_name": guest.name,
            "guest_email": guest.email,
            "booking_code": booking.booking_code,
            "reason": cancellation.reason,
            "refund_percentage": float(cancellation.refund_percentage),
            "refund_amount": float(cancellation.refund_amount),
            "refund_status": cancellation.refund_status.value,
        })

        refund_chain = chain(
            process_refund.s(str(cancellation.id)),
            notify_waitlist_on_cancellation.s(
                str(booking.room_id),
                str(booking.check_in_date),
                str(booking.check_out_date),
            )
        )
        refund_chain.delay()

        await db.refresh(cancellation)
        return cancellation

    async def get_by_id(self, db: AsyncSession, cancellation_id: UUID) -> Cancellation:
        result = await db.execute(
            select(Cancellation).where(Cancellation.id == cancellation_id)
        )
        cancellation = result.scalar_one_or_none()
        if not cancellation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cancellation tidak ditemukan"
            )
        return cancellation

    async def approve_refund(self, db: AsyncSession, cancellation_id: UUID) -> Cancellation:
        cancellation = await self.get_by_id(db, cancellation_id)
        if cancellation.refund_status != RefundStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund sudah diproses sebelumnya"
            )

        from app.tasks.refund_tasks import process_refund_approved
        process_refund_approved.delay(str(cancellation_id))

        await db.refresh(cancellation)
        return cancellation


cancellation_service = CancellationService()