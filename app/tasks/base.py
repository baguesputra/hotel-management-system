import logging
from celery import Task
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


class BaseTaskWithRetry(Task):
    """
    Base class untuk semua Celery tasks.
    Menyediakan exponential backoff dan error logging otomatis.
    """
    abstract = True
    max_retries = 3

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Dipanggil saat task benar-benar gagal (sudah habis retry)."""
        logger.error(
            f"Task permanently FAILED | "
            f"task={self.name} | "
            f"task_id={task_id} | "
            f"error={str(exc)} | "
            f"args={args}"
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Dipanggil setiap kali task akan di-retry."""
        logger.warning(
            f"Task RETRYING | "
            f"task={self.name} | "
            f"task_id={task_id} | "
            f"attempt={self.request.retries + 1}/{self.max_retries} | "
            f"error={str(exc)}"
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Dipanggil saat task berhasil."""
        logger.info(
            f"Task SUCCESS | "
            f"task={self.name} | "
            f"task_id={task_id}"
        )
        super().on_success(retval, task_id, args, kwargs)

    def get_retry_countdown(self, retries: int) -> int:
        """
        Exponential backoff calculation.
        retry 1 → 60 detik
        retry 2 → 120 detik
        retry 3 → 240 detik
        """
        return 60 * (2 ** retries)