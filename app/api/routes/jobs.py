from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.celery_app import celery_app
from app.tasks.sample_tasks import ping, simulate_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None
    error: str | None = None


class SimulateJobRequest(BaseModel):
    duration: int = 5
    job_name: str = "test"


@router.post("/ping", status_code=202)
async def trigger_ping():
    """Trigger task ping — verifikasi Celery berjalan."""
    task = ping.delay()
    return {
        "message": "Task dikirim ke worker",
        "task_id": task.id
    }


@router.post("/simulate", status_code=202)
async def trigger_simulate(data: SimulateJobRequest):
    """Trigger simulasi job dengan durasi tertentu."""
    task = simulate_job.delay(
        duration=data.duration,
        job_name=data.job_name
    )
    return {
        "message": "Task dikirim ke worker",
        "task_id": task.id
    }


@router.get("/{task_id}", response_model=JobStatusResponse)
async def get_job_status(task_id: str):
    """Cek status task by ID."""
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == "PENDING":
        return JobStatusResponse(
            task_id=task_id,
            status="PENDING",
        )
    elif task_result.state == "PROGRESS":
        return JobStatusResponse(
            task_id=task_id,
            status="PROGRESS",
            result=task_result.info,
        )
    elif task_result.state == "SUCCESS":
        return JobStatusResponse(
            task_id=task_id,
            status="SUCCESS",
            result=task_result.result,
        )
    elif task_result.state == "FAILURE":
        return JobStatusResponse(
            task_id=task_id,
            status="FAILURE",
            error=str(task_result.info),
        )
    else:
        return JobStatusResponse(
            task_id=task_id,
            status=task_result.state,
        )