"""
User Limits Service
────────────────────
Free:  10 searches/day
Pro:   50 searches/day  (جاهز للمستقبل)
"""

import aiosqlite
from backend.core.database import DB_PATH

LIMITS = {
    "free": 10,
    "pro":  50,
}


async def get_search_count_today(user_id: str) -> int:
    """كام بحث عمله المستخدم النهارده."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT COUNT(*) FROM user_searches
            WHERE user_id = ?
              AND date(searched_at) = date('now')
        """, (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0


async def can_search(user_id: str, plan: str = "free") -> tuple[bool, str]:
    """
    هل المستخدم عنده searches متبقية؟
    Returns: (allowed, message)
    """
    limit = LIMITS.get(plan, LIMITS["free"])
    count = await get_search_count_today(user_id)

    if count >= limit:
        return False, f"Daily limit reached ({limit} searches/day). Upgrade for more."
    return True, f"{limit - count} searches remaining today"


async def record_search(user_id: str, query: str, result_count: int = 0):
    """سجّل بحث جديد للمستخدم."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_searches (user_id, query, result_count)
            VALUES (?, ?, ?)
        """, (user_id, query.strip().lower(), result_count))
        await db.commit()


async def get_popular_searches(limit: int = 10) -> list:
    """أكثر الـ queries شيوعاً — للـ suggestions."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT query, COUNT(*) as count
            FROM user_searches
            WHERE date(searched_at) >= date('now', '-7 days')
            GROUP BY query
            ORDER BY count DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_user_history(user_id: str, limit: int = 10) -> list:
    """آخر بحثات المستخدم."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT query, result_count, searched_at
            FROM user_searches
            WHERE user_id = ?
            ORDER BY searched_at DESC
            LIMIT ?
        """, (user_id, limit))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
