from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import guests, rooms, bookings, payments, cancellations, waitlist, jobs

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Hotel Management System with Background Job Processing",
)

API_PREFIX = "/api/v1"

app.include_router(guests.router, prefix=API_PREFIX)
app.include_router(rooms.router, prefix=API_PREFIX)
app.include_router(bookings.router, prefix=API_PREFIX)
app.include_router(payments.router, prefix=API_PREFIX)
app.include_router(cancellations.router, prefix=API_PREFIX)
app.include_router(waitlist.router, prefix=API_PREFIX)
app.include_router(jobs.router, prefix=API_PREFIX)


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }