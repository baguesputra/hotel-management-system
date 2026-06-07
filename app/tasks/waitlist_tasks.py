import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.notify_waitlist_on_cancellation",
    max_retries=3,
    default_retry_delay=30,
)
def notify_waitlist_on_cancellation(self, room_id: str, check_in_date: str, check_out_date: str) -> dict:
    """
    Task 3 dari chain:
    Cek waitlist untuk room + tanggal yang baru tersedia.
    Kirim notifikasi ke semua guest yang menunggu.
    """
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import and_
    from app.models.waitlist import Waitlist, WaitlistStatus
    from app.models.guest import Guest
    from app.models.room import Room
    from app.core.config import settings
    from app.tasks.email_tasks import send_waitlist_notification

    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)

    notified_count = 0

    try:
        with Session() as session:
            # ambil semua waitlist entry untuk room + tanggal ini
            entries = session.query(Waitlist).filter(
                and_(
                    Waitlist.room_id == room_id,
                    Waitlist.check_in_date == check_in_date,
                    Waitlist.status == WaitlistStatus.WAITING,
                )
            ).all()

            if not entries:
                logger.info(f"Tidak ada waitlist untuk room {room_id} tanggal {check_in_date}")
                return {"notified": 0}

            room = session.get(Room, room_id)
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=24)

            for entry in entries:
                guest = session.get(Guest, str(entry.guest_id))
                if not guest:
                    continue

                # update status waitlist
                entry.status = WaitlistStatus.NOTIFIED
                entry.notified_at = now
                entry.expires_at = expires_at

                # kirim email notifikasi
                send_waitlist_notification.delay({
                    "guest_name": guest.name,
                    "guest_email": guest.email,
                    "room_number": room.room_number,
                    "room_type": room.room_type.value,
                    "check_in_date": str(entry.check_in_date),
                    "check_out_date": str(entry.check_out_date),
                    "expires_at": expires_at.strftime("%d %B %Y %H:%M WIB"),
                })
                notified_count += 1

            session.commit()

        logger.info(f"Waitlist notifikasi terkirim: {notified_count} guest")
        return {"notified": notified_count}

    except Exception as exc:
        logger.error(f"Gagal notify waitlist: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(name="tasks.expire_waitlist_entries")
def expire_waitlist_entries() -> dict:
    """
    Periodic task — jalan setiap jam.
    Auto-expire waitlist entry yang sudah lewat 24 jam setelah dinotifikasi.
    """
    from datetime import datetime, timezone
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.waitlist import Waitlist, WaitlistStatus
    from app.core.config import settings

    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)

    expired_count = 0

    with Session() as session:
        now = datetime.now(timezone.utc)
        entries = session.query(Waitlist).filter(
            Waitlist.status == WaitlistStatus.NOTIFIED,
            Waitlist.expires_at <= now,
        ).all()

        for entry in entries:
            entry.status = WaitlistStatus.EXPIRED
            expired_count += 1

        session.commit()

    logger.info(f"Waitlist entries expired: {expired_count}")
    return {"expired": expired_count}