import logging
from app.celery_app import celery_app
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.send_booking_confirmation",
    max_retries=3,
    default_retry_delay=60,
)
def send_booking_confirmation(self, booking_data: dict) -> dict:
    """Kirim email konfirmasi booking."""
    try:
        email_service.send(
            to_email=booking_data["guest_email"],
            to_name=booking_data["guest_name"],
            subject=f"Konfirmasi Booking {booking_data['booking_code']}",
            template_name="booking_confirmation.html",
            context=booking_data,
        )
        return {"status": "sent", "to": booking_data["guest_email"]}
    except Exception as exc:
        logger.error(f"Gagal kirim booking confirmation: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="tasks.send_payment_receipt",
    max_retries=3,
    default_retry_delay=60,
)
def send_payment_receipt(self, payment_data: dict) -> dict:
    """Kirim email receipt pembayaran."""
    try:
        email_service.send(
            to_email=payment_data["guest_email"],
            to_name=payment_data["guest_name"],
            subject=f"Konfirmasi Pembayaran - {payment_data['booking_code']}",
            template_name="payment_receipt.html",
            context=payment_data,
        )
        return {"status": "sent", "to": payment_data["guest_email"]}
    except Exception as exc:
        logger.error(f"Gagal kirim payment receipt: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="tasks.send_check_in_welcome",
    max_retries=3,
    default_retry_delay=60,
)
def send_check_in_welcome(self, checkin_data: dict) -> dict:
    """Kirim email welcome saat check-in."""
    try:
        email_service.send(
            to_email=checkin_data["guest_email"],
            to_name=checkin_data["guest_name"],
            subject="Selamat Datang di Hotel Kami!",
            template_name="check_in_welcome.html",
            context=checkin_data,
        )
        return {"status": "sent", "to": checkin_data["guest_email"]}
    except Exception as exc:
        logger.error(f"Gagal kirim check-in welcome: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="tasks.send_booking_reminder",
    max_retries=3,
    default_retry_delay=60,
)
def send_booking_reminder(self, reminder_data: dict) -> dict:
    """Kirim email reminder H-1 sebelum check-in."""
    try:
        email_service.send(
            to_email=reminder_data["guest_email"],
            to_name=reminder_data["guest_name"],
            subject=f"Reminder Check-in Besok - {reminder_data['booking_code']}",
            template_name="booking_reminder.html",
            context=reminder_data,
        )
        return {"status": "sent", "to": reminder_data["guest_email"]}
    except Exception as exc:
        logger.error(f"Gagal kirim booking reminder: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="tasks.send_refund_confirmation",
    max_retries=3,
    default_retry_delay=60,
)
def send_refund_confirmation(self, refund_data: dict) -> dict:
    """Kirim email konfirmasi refund."""
    try:
        email_service.send(
            to_email=refund_data["guest_email"],
            to_name=refund_data["guest_name"],
            subject=f"Konfirmasi Pembatalan - {refund_data['booking_code']}",
            template_name="refund_confirmation.html",
            context=refund_data,
        )
        return {"status": "sent", "to": refund_data["guest_email"]}
    except Exception as exc:
        logger.error(f"Gagal kirim refund confirmation: {exc}")
        raise self.retry(exc=exc)

@celery_app.task(name="tasks.send_daily_reminders")
def send_daily_reminders() -> dict:
    """
    Periodic task — jalan setiap hari jam 08.00.
    Cari semua booking dengan check-in besok dan kirim reminder.
    """
    from datetime import date, timedelta
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.booking import Booking, BookingStatus
    from app.models.guest import Guest
    from app.models.room import Room
    from app.core.config import settings

    # gunakan sync engine untuk periodic task
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)

    sent_count = 0
    with Session() as session:
        tomorrow = date.today() + timedelta(days=1)
        bookings = session.query(Booking).filter(
            Booking.check_in_date == tomorrow,
            Booking.status == BookingStatus.CONFIRMED,
        ).all()

        for booking in bookings:
            guest = session.get(Guest, booking.guest_id)
            room = session.get(Room, booking.room_id)

            if guest and room:
                send_booking_reminder.delay({
                    "guest_name": guest.name,
                    "guest_email": guest.email,
                    "booking_code": booking.booking_code,
                    "room_number": room.room_number,
                    "room_type": room.room_type.value,
                    "check_in_date": str(booking.check_in_date),
                    "check_out_date": str(booking.check_out_date),
                })
                sent_count += 1

    logger.info(f"Reminder terkirim: {sent_count} booking")
    return {"reminders_sent": sent_count}

@celery_app.task(
    bind=True,
    name="tasks.send_waitlist_notification",
    max_retries=3,
    default_retry_delay=60,
)
def send_waitlist_notification(self, notification_data: dict) -> dict:
    """Kirim email notifikasi ke guest di waitlist."""
    try:
        email_service.send(
            to_email=notification_data["guest_email"],
            to_name=notification_data["guest_name"],
            subject=f"Kamar Tersedia! Segera Booking",
            template_name="waitlist_notification.html",
            context=notification_data,
        )
        return {"status": "sent", "to": notification_data["guest_email"]}
    except Exception as exc:
        logger.error(f"Gagal kirim waitlist notification: {exc}")
        raise self.retry(exc=exc)