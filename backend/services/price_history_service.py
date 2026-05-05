import logging
import aiosqlite
from typing import List, Dict, Optional
from backend.core.database import DB_PATH

logger = logging.getLogger(__name__)


async def record_price(product: Dict):
    """Save a price snapshot for a product every time it's scored."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO price_history
                (product_id, product_title, ebay_price, estimated_cost, profit, final_score, verdict)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            product.get("id"),
            product.get("title", "")[:120],
            product.get("ebay_price"),
            product.get("estimated_cost"),
            product.get("profit"),
            product.get("final_score"),
            product.get("verdict"),
        ))
        await db.commit()


async def get_price_history(product_id: str, days: int = 30) -> List[Dict]:
    """Return price snapshots for a product over the last N days."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT ebay_price, estimated_cost, profit, final_score, verdict, recorded_at
            FROM price_history
            WHERE product_id = ?
              AND datetime(recorded_at) >= datetime('now', ? || ' days')
            ORDER BY recorded_at ASC
        """, (product_id, f"-{days}"))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_price_trend(product_id: str) -> Dict:
    """
    Returns trend summary: direction / change_pct / min_price / max_price / data_points.
    Safe against: empty history, single data point, zero prices, None values.
    """
    history = await get_price_history(product_id, days=30)

    # Filter out None/zero prices before any calculation
    prices = [
        h["ebay_price"]
        for h in history
        if h.get("ebay_price") is not None and h["ebay_price"] > 0
    ]

    # Not enough data for a trend
    if len(prices) < 2:
        return {
            "direction":   "stable",
            "change_pct":  0.0,
            "min_price":   round(prices[0], 2) if prices else None,
            "max_price":   round(prices[0], 2) if prices else None,
            "data_points": len(prices),
        }

    first, last = prices[0], prices[-1]

    # Guard: first == 0 would cause ZeroDivisionError
    if first == 0:
        change_pct = 0.0
    else:
        change_pct = round(((last - first) / first) * 100, 2)

    direction = "stable"
    if change_pct > 3:
        direction = "rising"
    elif change_pct < -3:
        direction = "falling"

    return {
        "direction":   direction,
        "change_pct":  change_pct,
        "min_price":   round(min(prices), 2),
        "max_price":   round(max(prices), 2),
        "data_points": len(prices),
    }


async def cleanup_old_history(keep_days: int = 60):
    """Remove price history older than keep_days."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            DELETE FROM price_history
            WHERE datetime(recorded_at) < datetime('now', ? || ' days')
        """, (f"-{keep_days}",))
        await db.commit()
        logger.info("Removed %d old price history records", cursor.rowcount)
