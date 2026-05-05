import asyncio
import logging
from backend.core.config import settings

logger = logging.getLogger(__name__)


async def start_scheduler():
    """Background scheduler — runs full update every N hours."""
    await asyncio.sleep(10)

    while True:
        try:
            from backend.services.pipeline import run_full_update
            from backend.services.cache_service import cleanup_stale_cache
            from backend.services.abuse_service import cleanup_expired_blocks

            logger.info("⏰ Scheduler cycle starting…")
            await run_full_update()
            await cleanup_stale_cache()
            await cleanup_expired_blocks()
            logger.info("✅ Scheduler cycle complete")

        except Exception as e:
            logger.error("Scheduler error: %s", e)
            await asyncio.sleep(60)   # لو error متكرر → مش infinite tight loop

        wait = settings.UPDATE_INTERVAL_HOURS * 3600
        logger.info("⏰ Next cycle in %dh", settings.UPDATE_INTERVAL_HOURS)
        await asyncio.sleep(wait)
