from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.outbox.dependencies import get_outbox_dispatcher

# TODO: when the project adopts a task manager, replace APScheduler with its
# built-in scheduler and remove the APScheduler dependency. Consider pgqueuer
# as an Outbox implementation: it can receive a raw asyncpg connection from
# SQLAlchemy.
MAX_CONCURRENT_DISPATCHES = 1

scheduler = AsyncIOScheduler()


@scheduler.scheduled_job(
    'interval',
    seconds=1,
    id='outbox-dispatch',
    coalesce=True,
    max_instances=MAX_CONCURRENT_DISPATCHES,
    misfire_grace_time=None,
    next_run_time=datetime.now(timezone.utc),
)
async def dispatch_outbox() -> None:
    async with get_outbox_dispatcher() as dispatcher:
        await dispatcher.dispatch_once()
