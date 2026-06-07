from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.cancellation import CancellationCreate, CancellationResponse
from app.services.cancellation_service import cancellation_service
from celery.result import AsyncResult
from app.celery_app import celery_app

router = APIRouter(prefix="/cancellations", tags=["Cancellations"])


@router.post("", response_model=CancellationResponse, status_code=201)
async def cancel_booking(data: CancellationCreate, db: AsyncSession = Depends(get_db)):
    return await cancellation_service.create(db, data)


@router.get("/{cancellation_id}", response_model=CancellationResponse)
async def get_cancellation(cancellation_id: UUID, db: AsyncSession = Depends(get_db)):
    return await cancellation_service.get_by_id(db, cancellation_id)


@router.patch("/{cancellation_id}/approve", response_model=CancellationResponse)
async def approve_refund(cancellation_id: UUID, db: AsyncSession = Depends(get_db)):
    return await cancellation_service.approve_refund(db, cancellation_id)

@router.get("/{cancellation_id}/task-status")
async def get_cancellation_task_status(cancellation_id: UUID):
    """Cek status background task yang terkait dengan cancellation."""
    # format task id yang kita pakai
    task_id = f"refund-{cancellation_id}"
    task_result = AsyncResult(task_id, app=celery_app)
    return {
        "cancellation_id": str(cancellation_id),
        "task_status": task_result.state,
    }