import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.process_refund",
    max_retries=3,
    default_retry_delay=60,
)
def process_refund(self, cancellation_id: str) -> dict:
    """
    Task 1 dari chain:
    Proses refund — update status cancellation jadi APPROVED.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.cancellation import Cancellation, RefundStatus
    from app.core.config import settings

    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)

    try:
        with Session() as session:
            cancellation = session.get(Cancellation, cancellation_id)
            if not cancellation:
                raise ValueError(f"Cancellation {cancellation_id} tidak ditemukan")

            cancellation.refund_status = RefundStatus.APPROVED
            session.commit()

            logger.info(f"Refund diproses untuk cancellation {cancellation_id}")
            return {
                "cancellation_id": cancellation_id,
                "refund_status": "approved",
                "refund_amount": float(cancellation.refund_amount),
            }
    except Exception as exc:
        logger.error(f"Gagal proses refund: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="tasks.process_refund_approved",
    max_retries=3,
    default_retry_delay=60,
)
def process_refund_approved(self, cancellation_id: str) -> dict:
    """
    Task yang dijalankan saat staff approve refund manual.
    Update status jadi PROCESSED dan kirim email notifikasi.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.cancellation import Cancellation, RefundStatus
    from app.models.booking import Booking
    from app.models.guest import Guest
    from app.core.config import settings
    from app.tasks.email_tasks import send_refund_confirmation

    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)

    try:
        with Session() as session:
            cancellation = session.get(Cancellation, cancellation_id)
            if not cancellation:
                raise ValueError(f"Cancellation {cancellation_id} tidak ditemukan")

            cancellation.refund_status = RefundStatus.PROCESSED
            session.commit()

            # ambil data untuk email
            booking = session.get(Booking, str(cancellation.booking_id))
            guest = session.get(Guest, str(booking.guest_id))

            # trigger email notifikasi refund processed
            send_refund_confirmation.delay({
                "guest_name": guest.name,
                "guest_email": guest.email,
                "booking_code": booking.booking_code,
                "reason": cancellation.reason,
                "refund_percentage": float(cancellation.refund_percentage),
                "refund_amount": float(cancellation.refund_amount),
                "refund_status": "PROCESSED - Akan ditransfer dalam 3-5 hari kerja",
            })

            logger.info(f"Refund approved & processed untuk cancellation {cancellation_id}")
            return {
                "cancellation_id": cancellation_id,
                "refund_status": "processed",
            }
    except Exception as exc:
        logger.error(f"Gagal approve refund: {exc}")
        raise self.retry(exc=exc)