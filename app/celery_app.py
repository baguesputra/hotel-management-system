from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "hotel",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.sample_tasks",  # tambah di sini setiap ada module tasks baru
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Makassar",
    enable_utc=True,
    task_track_started=True,        # task punya status STARTED sebelum SUCCESS
    task_acks_late=True,            # task di-acknowledge setelah selesai, bukan sebelum
    worker_prefetch_multiplier=1,   # worker ambil 1 task per worker, tidak greedy
    result_expires=3600,            # result disimpan 1 jam di Redis
)