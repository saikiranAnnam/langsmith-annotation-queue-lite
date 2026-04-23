import asyncio
import logging 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def requeue_stuck_entries(pool, stale_after_seconds: int) -> int:
    """Every interval, requeue in_progress entries older than the threshold."""
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE queue_entries
            SET status = 'pending',
                reserved_at = NULL,
                reserved_by = NULL
            WHERE status = 'in_progress'
            AND reserved_by IS NOT NULL
            AND reserved_at < NOW() - ($1 * interval '1 second')
            """,
            stale_after_seconds,
        )
    count = int(result.split()[-1])
    logger.info(f"Requeued {count} stuck entries")
    return count

async def requeue_stuck_entries_loop(
    pool, 
    interval_seconds: int,
    stale_after_seconds: int,
    stop_event: asyncio.Event,
) -> None:
    """Run the requeue_stuck_entries job in a loop."""
    logger.info("Starting stuck-entry requeue loop: interval=%s, stale_after=%s", 
        interval_seconds, 
        stale_after_seconds)
    while not stop_event.is_set():
        try:
            await requeue_stuck_entries(pool, stale_after_seconds)
        except Exception as e:
            logger.error(f"Failed to requeue stuck queue entries: {e}")        
        
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            pass

    logger.info("Stopping stuck-entry requeue loop")