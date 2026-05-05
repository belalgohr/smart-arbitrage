"""
Smart Cache Service
───────────────────
- TTL مختلف لكل نوع بيانات
- Query normalization قبل الحفظ
- توفير 80%+ من eBay API calls
"""

import logging
import aiosqlite
import json
import re
from typing import Optional, List, Dict
from backend.core.database import DB_PATH

# ── TTL بالساعات لكل نوع ─────────────────────────────────
CACHE_TTL = {
    "search":  6,   # نتايج البحث العادي
    "deals":   3,   # الـ top deals (بتتغير أسرع)
    "product": 12,  # بيانات منتج معين
}

# ── Query Normalization ──────────────────────────────────

def normalize_query(query: str) -> str:
    """
    تحويل الـ query لشكل موحد قبل الحفظ والبحث
    "  Wireless  Earbuds!! " → "wireless earbuds"
    """
    q = query.lower().strip()
    q = re.sub(r"[^\w\s]", "", q)        # شيل الرموز
    q = re.sub(r"\s+", " ", q)           # spaces متعددة → واحدة
    return q


def queries_are_similar(q1: str, q2: str) -> bool:
    """
    هل استعلامين بيقصدوا نفس الحاجة؟
    مثال: "wireless earbuds" ≈ "earbuds wireless"
    بدون embeddings — word overlap بسيط وسريع
    """
    words1 = set(normalize_query(q1).split())
    words2 = set(normalize_query(q2).split())
    if not words1 or not words2:
        return False
    overlap = len(words1 & words2) / max(len(words1), len(words2))
    return overlap >= 0.8


# ── Cache Operations ─────────────────────────────────────

async def get_cached(query: str, cache_type: str = "search") -> Optional[List[Dict]]:
    """
    رجّع النتايج من الـ cache لو موجودة وطازجة.
    None = cache miss أو منتهية الصلاحية.
    """
    key  = normalize_query(query)
    ttl  = CACHE_TTL.get(cache_type, 6)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT results FROM search_cache
            WHERE query = ?
              AND datetime(last_updated) >= datetime('now', ? || ' hours')
        """, (key, f"-{ttl}"))
        row = await cursor.fetchone()

    if not row:
        return None
    try:
        return json.loads(row["results"])
    except Exception:
        return None


async def set_cached(query: str, products: List[Dict], cache_type: str = "search"):
    """احفظ النتايج في الـ cache."""
    key     = normalize_query(query)
    payload = json.dumps(products, ensure_ascii=False)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO search_cache (query, results, product_count, last_updated)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(query) DO UPDATE SET
                results       = excluded.results,
                product_count = excluded.product_count,
                last_updated  = CURRENT_TIMESTAMP
        """, (key, payload, len(products)))
        await db.commit()


async def invalidate(query: str):
    """اجبر الـ cache entry إنها تنتهي فوراً."""
    key = normalize_query(query)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE search_cache
            SET last_updated = datetime('now', '-100 hours')
            WHERE query = ?
        """, (key,))
        await db.commit()


async def find_similar_cached(query: str, cache_type: str = "search") -> Optional[List[Dict]]:
    """
    ابحث عن query مشابه في الـ cache.
    لو مفيش exact match → ابحث عن word overlap >= 80%
    بيوفر calls لمنتجات متشابهة
    """
    # أول حاول exact
    result = await get_cached(query, cache_type)
    if result is not None:
        return result

    # لو مفيش → search عن مشابه
    ttl = CACHE_TTL.get(cache_type, 6)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT query, results FROM search_cache
            WHERE datetime(last_updated) >= datetime('now', ? || ' hours')
        """, (f"-{ttl}",))
        rows = await cursor.fetchall()

    for row in rows:
        if queries_are_similar(query, row["query"]):
            try:
                return json.loads(row["results"])
            except Exception:
                continue
    return None


async def get_cache_stats() -> Dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM search_cache")
        total  = (await cursor.fetchone())[0]

        cursor = await db.execute("""
            SELECT COUNT(*) FROM search_cache
            WHERE datetime(last_updated) >= datetime('now', '-6 hours')
        """)
        fresh = (await cursor.fetchone())[0]

    return {
        "total_cached_queries": total,
        "fresh_entries":        fresh,
        "ttl_config":           CACHE_TTL,
    }


async def cleanup_stale_cache(max_age_hours: int = 48):
    """احذف entries قديمة جداً."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            DELETE FROM search_cache
            WHERE datetime(last_updated) < datetime('now', ? || ' hours')
        """, (f"-{max_age_hours}",))
        await db.commit()
        if cursor.rowcount:
            logging.getLogger(__name__).info("Cache: removed %d stale entries", cursor.rowcount)
