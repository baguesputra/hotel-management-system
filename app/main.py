import redis as redis_client
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
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
    """Basic health check."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


@app.get("/health/detailed", tags=["System"])
async def detailed_health_check():
    """
    Detailed health check — cek semua komponen:
    database, redis, dan celery worker.
    """
    health = {
        "app": "ok",
        "database": "unknown",
        "redis": "unknown",
        "celery": "unknown",
    }

    # cek database
    try:
        engine = create_async_engine(settings.database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        health["database"] = "ok"
    except Exception as e:
        health["database"] = f"error: {str(e)}"

    # cek redis
    try:
        r = redis_client.from_url(settings.redis_url)
        r.ping()
        health["redis"] = "ok"
    except Exception as e:
        health["redis"] = f"error: {str(e)}"

    # cek celery worker
    try:
        from app.celery_app import celery_app
        inspector = celery_app.control.inspect(timeout=2)
        active_workers = inspector.ping()
        if active_workers:
            health["celery"] = f"ok ({len(active_workers)} worker)"
        else:
            health["celery"] = "no workers found"
    except Exception as e:
        health["celery"] = f"error: {str(e)}"

    overall = "ok" if all(v == "ok" or "ok" in str(v) for v in health.values()) else "degraded"

    return {
        "status": overall,
        "components": health,
    }