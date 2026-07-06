from celery import Celery
from celery.schedules import crontab
from celery.signals import task_failure, task_retry, task_success
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

celery_app = Celery(
    "hotel",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.sample_tasks",
        "app.tasks.email_tasks",
        "app.tasks.refund_tasks",
        "app.tasks.waitlist_tasks",
        "app.tasks.report_tasks",
    ],
)

celery_app.conf.update(
    # serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # timezone
    timezone="Asia/Makassar",
    enable_utc=True,

    # task tracking
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # result expiry
    result_expires=86400,  # 24 jam

    # retry defaults
    task_max_retries=3,

    # dead letter queue
    task_routes={
        "tasks.*": {"queue": "celery"},
    },

    # broker connection retry
    broker_connection_retry_on_startup=True,

    # task time limits
    task_soft_time_limit=300,  # 5 menit soft limit
    task_time_limit=600,       # 10 menit hard limit
)

celery_app.conf.beat_schedule = {
    "send-booking-reminders-daily": {
        "task": "tasks.send_daily_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    "expire-waitlist-entries-hourly": {
        "task": "tasks.expire_waitlist_entries",
        "schedule": crontab(minute=0),
    },
    "generate-monthly-report": {
        "task": "tasks.generate_monthly_report",
        "schedule": crontab(day_of_month=1, hour=7, minute=0),
    },
}


# ─── Global Signal Handlers ───────────────────────────────────────────────────

@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    """Log semua task failure di satu tempat."""
    logger.error(
        f"Task FAILED | "
        f"task={sender.name} | "
        f"task_id={task_id} | "
        f"error={str(exception)}"
    )


@task_retry.connect
def on_task_retry(sender=None, request=None, reason=None, **kwargs):
    """Log setiap kali task di-retry."""
    logger.warning(
        f"Task RETRY | "
        f"task={sender.name} | "
        f"task_id={request.id} | "
        f"reason={str(reason)} | "
        f"retries={request.retries}"
    )


@task_success.connect
def on_task_success(sender=None, result=None, **kwargs):
    """Log task success."""
    logger.info(
        f"Task SUCCESS | "
        f"task={sender.name}"
    )