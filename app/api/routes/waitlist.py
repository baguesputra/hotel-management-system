from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.waitlist import WaitlistCreate, WaitlistResponse
from app.services.waitlist_service import waitlist_service

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post("", response_model=WaitlistResponse, status_code=201)
async def join_waitlist(data: WaitlistCreate, db: AsyncSession = Depends(get_db)):
    return await waitlist_service.join(db, data)


@router.get("/{waitlist_id}", response_model=WaitlistResponse)
async def get_waitlist_entry(waitlist_id: UUID, db: AsyncSession = Depends(get_db)):
    entry = await waitlist_service.get_by_id(db, waitlist_id)
    position = await waitlist_service.get_position(db, waitlist_id)
    response = WaitlistResponse.model_validate(entry)
    response.position = position
    return response


@router.delete("/{waitlist_id}", status_code=204)
async def cancel_waitlist(waitlist_id: UUID, db: AsyncSession = Depends(get_db)):
    await waitlist_service.cancel(db, waitlist_id)