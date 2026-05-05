import logging
import aiosqlite
from typing import List, Dict, Optional
from backend.core.database import DB_PATH
from backend.core.config import settings
from datetime import datetime

async def save_product(product: Dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO products (
                id, title, image_url, ebay_price, estimated_cost, shipping_cost,
                profit, demand_score, trend_score, competition_score, final_score,
                reviews_count, rating, seller_count, category, relevance_score,
                verdict, ebay_url, last_updated
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, CURRENT_TIMESTAMP)
        """, (
            product.get("id"),
            product.get("title"),
            product.get("image_url"),
            product.get("ebay_price"),
            product.get("estimated_cost"),
            product.get("shipping_cost"),
            product.get("profit"),
            product.get("demand_score"),
            product.get("trend_score"),
            product.get("competition_score"),
            product.get("final_score"),
            product.get("reviews_count"),
            product.get("rating"),
            product.get("seller_count"),
            product.get("category"),
            product.get("relevance_score"),
            product.get("verdict"),
            product.get("ebay_url"),
        ))
        await db.commit()


async def save_products_bulk(products: List[Dict]):
    """
    Bulk insert/replace — connection مفتوحة مرة واحدة بس.
    أسرع بكتير من loop فيه save_product لكل عنصر.
    """
    if not products:
        return

    rows = [
        (
            p.get("id"),
            p.get("title"),
            p.get("image_url"),
            p.get("ebay_price"),
            p.get("estimated_cost"),
            p.get("shipping_cost"),
            p.get("profit"),
            p.get("demand_score"),
            p.get("trend_score"),
            p.get("competition_score"),
            p.get("final_score"),
            p.get("reviews_count"),
            p.get("rating"),
            p.get("seller_count"),
            p.get("category"),
            p.get("relevance_score"),
            p.get("verdict"),
            p.get("ebay_url"),
        )
        for p in products
    ]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany("""
            INSERT OR REPLACE INTO products (
                id, title, image_url, ebay_price, estimated_cost, shipping_cost,
                profit, demand_score, trend_score, competition_score, final_score,
                reviews_count, rating, seller_count, category, relevance_score,
                verdict, ebay_url, last_updated
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, CURRENT_TIMESTAMP)
        """, rows)
        await db.commit()


async def get_products(
    query: str = "",
    verdict: str = "",
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    limit = min(limit, 100)   # cap — user مش يقدر يبعت limit=999999
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        conditions = ["1=1"]
        params = []

        if query:
            conditions.append("LOWER(title) LIKE ?")
            params.append(f"%{query.lower()}%")
        if verdict:
            conditions.append("verdict = ?")
            params.append(verdict.upper())

        where = " AND ".join(conditions)
        params.extend([limit, offset])

        cursor = await db.execute(f"""
            SELECT * FROM products
            WHERE {where}
            ORDER BY final_score DESC
            LIMIT ? OFFSET ?
        """, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_top_deals(limit: int = 20) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM products
            WHERE verdict = 'BUY'
            AND profit > 5
            ORDER BY final_score DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_top_today(limit: int = 10) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM products
            WHERE verdict = 'BUY'
            AND datetime(last_updated) >= datetime('now', '-24 hours')
            ORDER BY final_score DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_stats() -> Dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM products")
        total = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM products WHERE verdict='BUY'")
        buy_count = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT AVG(profit) FROM products WHERE verdict='BUY'")
        avg_profit = (await cursor.fetchone())[0] or 0

        cursor = await db.execute("SELECT MAX(final_score) FROM products")
        top_score = (await cursor.fetchone())[0] or 0

        return {
            "total_products": total,
            "buy_signals": buy_count,
            "avg_profit": round(avg_profit, 2),
            "top_score": round(top_score, 3)
        }


async def cleanup_old_products():
    """Remove products older than TTL"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            DELETE FROM products
            WHERE datetime(last_updated) < datetime('now', ? || ' hours')
        """, (f"-{settings.DATA_TTL_HOURS}",))
        deleted = cursor.rowcount
        await db.commit()

    # Keep max products — nested subquery آمن في SQLite
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            DELETE FROM products WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id FROM products
                    ORDER BY final_score DESC
                    LIMIT ?
                )
            )
        """, (settings.MAX_PRODUCTS,))
        await db.commit()

    logging.getLogger(__name__).info("Cleaned %d old products", deleted)
