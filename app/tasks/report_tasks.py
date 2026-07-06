import logging
from app.celery_app import celery_app
from app.tasks.base import BaseTaskWithRetry

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.generate_invoice",
    base=BaseTaskWithRetry,
    max_retries=3,
    default_retry_delay=60,
)
def generate_invoice(self, booking_id: str) -> dict:
    """Generate invoice PDF saat check-out."""
    from datetime import datetime
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.booking import Booking
    from app.models.guest import Guest
    from app.models.room import Room
    from app.models.payment import Payment
    from app.services.report_service import report_service
    from app.core.config import settings

    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)

    try:
        with Session() as session:
            booking = session.get(Booking, booking_id)
            guest = session.get(Guest, str(booking.guest_id))
            room = session.get(Room, str(booking.room_id))
            payment = session.query(Payment).filter(
                Payment.booking_id == booking.id
            ).first()

            context = {
                "booking_code": booking.booking_code,
                "invoice_date": datetime.now().strftime("%d %B %Y"),
                "guest_name": guest.name,
                "guest_email": guest.email,
                "guest_phone": guest.phone or "",
                "guest_address": guest.address or "",
                "room_number": room.room_number,
                "room_type": room.room_type.value,
                "check_in_date": booking.check_in_date.strftime("%d %B %Y"),
                "check_out_date": booking.check_out_date.strftime("%d %B %Y"),
                "total_nights": booking.total_nights,
                "price_per_night": float(booking.price_per_night),
                "total_amount": float(booking.total_amount),
                "payment_method": payment.payment_method.value if payment else "N/A",
                "payment_date": payment.updated_at.strftime("%d %B %Y") if payment else "N/A",
            }

            filepath = report_service.generate_invoice(context)

            logger.info(f"Invoice generated untuk booking {booking_id}: {filepath}")
            return {
                "status": "generated",
                "booking_id": booking_id,
                "filepath": filepath,
            }

    except Exception as exc:
        countdown = self.get_retry_countdown(self.request.retries)
        raise self.retry(exc=exc)


@celery_app.task(name="tasks.generate_monthly_report")
def generate_monthly_report() -> dict:
    """
    Periodic task — jalan setiap tanggal 1 jam 07.00.
    Generate laporan okupansi bulan sebelumnya.
    """
    from datetime import datetime, date
    from calendar import monthrange
    from sqlalchemy import create_engine, func
    from sqlalchemy.orm import sessionmaker
    from app.models.booking import Booking, BookingStatus
    from app.models.guest import Guest
    from app.models.room import Room
    from app.models.cancellation import Cancellation
    from app.services.report_service import report_service
    from app.core.config import settings

    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)

    # hitung periode bulan lalu
    today = date.today()
    if today.month == 1:
        year = today.year - 1
        month = 12
    else:
        year = today.year
        month = today.month - 1

    period = f"{year}-{month:02d}"
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])

    with Session() as session:
        # ambil semua booking di periode ini
        bookings = session.query(Booking).filter(
            Booking.check_in_date >= start_date,
            Booking.check_in_date <= end_date,
        ).all()

        total_revenue = sum(
            float(b.total_amount)
            for b in bookings
            if b.status in [BookingStatus.CHECKED_OUT, BookingStatus.CONFIRMED]
        )

        total_checkouts = sum(
            1 for b in bookings if b.status == BookingStatus.CHECKED_OUT
        )

        total_cancellations = sum(
            1 for b in bookings if b.status == BookingStatus.CANCELLED
        )

        # stats per room type
        room_type_data = {}
        for booking in bookings:
            room = session.get(Room, str(booking.room_id))
            if not room:
                continue
            rtype = room.room_type.value
            if rtype not in room_type_data:
                room_type_data[rtype] = {"count": 0, "revenue": 0}
            room_type_data[rtype]["count"] += 1
            if booking.status in [BookingStatus.CHECKED_OUT, BookingStatus.CONFIRMED]:
                room_type_data[rtype]["revenue"] += float(booking.total_amount)

        room_type_stats = [
            {
                "room_type": rtype,
                "booking_count": data["count"],
                "revenue": data["revenue"],
                "avg_per_booking": data["revenue"] / data["count"] if data["count"] > 0 else 0,
            }
            for rtype, data in room_type_data.items()
        ]

        # detail booking untuk tabel
        booking_details = []
        for booking in bookings:
            guest = session.get(Guest, str(booking.guest_id))
            room = session.get(Room, str(booking.room_id))
            booking_details.append({
                "booking_code": booking.booking_code,
                "guest_name": guest.name if guest else "N/A",
                "room_number": room.room_number if room else "N/A",
                "check_in_date": booking.check_in_date.strftime("%d %b %Y"),
                "check_out_date": booking.check_out_date.strftime("%d %b %Y"),
                "total_amount": float(booking.total_amount),
                "status": booking.status.value,
            })

        context = {
            "period": f"{start_date.strftime('%B %Y')}",
            "generated_at": datetime.now().strftime("%d %B %Y %H:%M"),
            "total_bookings": len(bookings),
            "total_revenue": total_revenue,
            "total_checkouts": total_checkouts,
            "total_cancellations": total_cancellations,
            "room_type_stats": room_type_stats,
            "bookings": booking_details,
        }

        filepath = report_service.generate_monthly_report(context, period)

        logger.info(f"Monthly report generated: {filepath}")
        return {
            "status": "generated",
            "period": period,
            "filepath": filepath,
            "total_bookings": len(bookings),
            "total_revenue": total_revenue,
        }