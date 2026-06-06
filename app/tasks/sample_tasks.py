import time
import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.ping")
def ping(self) -> dict:
    """Task sederhana untuk verifikasi Celery berjalan."""
    logger.info(f"Task ping dijalankan - task_id: {self.request.id}")
    return {"message": "pong", "task_id": self.request.id}


@celery_app.task(bind=True, name="tasks.simulate_job")
def simulate_job(self, duration: int = 5, job_name: str = "test") -> dict:
    """
    Simulasi task yang butuh waktu.
    Berguna untuk demo di Flower — bisa lihat task dalam status STARTED.
    """
    logger.info(f"Job '{job_name}' dimulai, durasi: {duration} detik")

    # update progress (bisa dipantau via Flower)
    self.update_state(
        state="PROGRESS",
        meta={"job_name": job_name, "status": "processing"}
    )

    time.sleep(duration)

    logger.info(f"Job '{job_name}' selesai")
    return {
        "job_name": job_name,
        "duration": duration,
        "status": "completed"
    }