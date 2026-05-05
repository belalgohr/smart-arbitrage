import random
import logging
import hashlib
import aiosqlite
from typing import List, Dict, Optional
from backend.models.product_repo import get_top_deals
from backend.core.database import DB_PATH

logger = logging.getLogger(__name__)

POOL_SIZE        = 100
USER_RECS        = 5
MAX_PER_CATEGORY = 2


def _user_seed(user_id: str) -> int:
    """Stable daily seed — same user sees same picks on same day."""
    from datetime import date
    raw = f"{user_id}:{date.today().isoformat()}"
    return int(hashlib.md5(raw.encode()).hexdigest(), 16) % (2 ** 31)


def _apply_diversity(products: List[Dict], max_per_cat: int = MAX_PER_CATEGORY) -> List[Dict]:
    """Max `max_per_cat` products per category."""
    seen: Dict[str, int] = {}
    result = []
    for p in products:
        cat = (p.get("category") or "General").strip().lower()
        if seen.get(cat, 0) < max_per_cat:
            result.append(p)
            seen[cat] = seen.get(cat, 0) + 1
    return result


async def get_recommendations(
    user_id: Optional[str] = None,
    count: int = USER_RECS,
) -> List[Dict]:
    """
    Personalised picks per user (daily seed + diversity filter).
    Fallback: if BUY pool is empty → return any top products.
    """
    pool = await get_top_deals(limit=POOL_SIZE)

    # Fallback: DB empty or no BUY deals yet → return top scored products
    if not pool:
        logger.info("Recommendations: BUY pool empty, using trending fallback")
        pool = await _any_top_products(limit=count)
        return pool[:count]

    seed = _user_seed(user_id or "anonymous")
    rng  = random.Random(seed)
    rng.shuffle(pool)

    diverse = _apply_diversity(pool, max_per_cat=MAX_PER_CATEGORY)
    return diverse[:count]


async def _any_top_products(limit: int) -> List[Dict]:
    """Any products ordered by score — used as fallback when no BUY deals."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM products
            ORDER BY final_score DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_trending(limit: int = 10) -> List[Dict]:
    pool = await get_top_deals(limit=limit)
    # Fallback: still show something if BUY pool is empty
    if not pool:
        return await _any_top_products(limit=limit)
    return pool


async def get_fresh_picks(limit: int = 10) -> List[Dict]:
    """Recently updated BUY products."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM products
            WHERE verdict = 'BUY'
            ORDER BY last_updated DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
