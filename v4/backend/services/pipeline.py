"""
Pipeline — Optimized v4
────────────────────────
Flow:
  1. normalize query
  2. cache check (exact → similar)     ← أول خطوة دايماً
  3. eBay fetch (20 items)
  4. pre-filter (بدون AI)
  5. AI batch (مرة واحدة على كل الـ products)
  6. score + AI fallback (منتج مش بيتحذف لو AI فشل)
  7. cache stores ALL scored results
  8. bulk DB save (مش loop)
  9. return top 5 فقط للـ user

Changes vs v3:
  - cache stores full scored list, not top 5
  - bulk DB insert via save_products_bulk
  - AI fallback: score product with empty ai_res if AI fails
  - proper logging instead of print()
"""

import asyncio
import logging
from typing import List, Dict

from backend.services.ebay_service          import search_ebay_products
from backend.services.ai_service            import classify_batch, _pre_filter
from backend.services.scoring_service       import score_product
from backend.services.price_history_service import record_price
from backend.services.cache_service         import find_similar_cached, set_cached, normalize_query
from backend.models.product_repo            import save_products_bulk, cleanup_old_products

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────
EBAY_FETCH_LIMIT = 20   # مش أكتر — API budget
TOP_N            = 5    # اللي بيرجعه للـ user
MIN_PROFIT       = 2.0
MIN_RELEVANCE    = 0.75
MIN_CONFIDENCE   = 0.65

DEFAULT_QUERIES = [
    "wireless earbuds", "phone case", "led strip lights",
    "portable charger", "smart watch", "kitchen gadgets",
    "fitness tracker", "bluetooth speaker", "home decor",
    "gaming accessories",
]


async def run_pipeline(
    query: str,
    limit: int = EBAY_FETCH_LIMIT,
    force_refresh: bool = False,
) -> List[Dict]:
    """
    Main pipeline. Cache-first. Returns top N products.
    Never crashes on partial failures.
    """
    norm = normalize_query(query)

    # ── Step 1: Cache (exact first, then similar) ─────────
    if not force_refresh:
        cached = await find_similar_cached(norm)
        if cached is not None:
            logger.info("Cache hit: '%s' → %d products", norm, len(cached))
            return cached[:TOP_N]

    logger.info("Pipeline start: '%s'", norm)

    # ── Step 2: eBay fetch ────────────────────────────────
    try:
        raw = await search_ebay_products(norm, limit=EBAY_FETCH_LIMIT)
    except Exception as e:
        logger.error("eBay fetch failed: %s", e)
        return []

    logger.info("Fetched %d items from eBay", len(raw))
    if not raw:
        return []

    # ── Step 3: Pre-filter (no AI needed) ────────────────
    pre = [p for p in raw if _pre_filter(p)]
    logger.info("Pre-filtered: %d → %d", len(raw), len(pre))

    # Fallback: لو pre-filter حذف كل حاجة → استخدم الـ raw
    # (أحسن من ما نرجع فاضي)
    if not pre:
        logger.info("Pre-filter returned empty — falling back to raw")
        pre = raw

    # ── Step 4: AI batch (one call for all products) ─────
    try:
        ai_results = await classify_batch(pre, concurrency=5)
    except Exception as e:
        logger.warning("AI batch failed: %s — using fallback for all", e)
        ai_results = [None] * len(pre)

    ai_valid = sum(1 for r in ai_results if r and r.get("is_valid"))
    logger.info("AI classified: %d/%d valid", ai_valid, len(pre))

    # ── Step 5: Merge + score (with fallback) ────────────
    scored = []
    for product, ai in zip(pre, ai_results):

        # AI fallback: لو AI فشل، مش بنحذف المنتج —
        # بنعمله score بـ empty ai_res (rule-based defaults)
        if not ai:
            logger.debug("AI fallback for: %s", product.get("title", "")[:40])
            ai = {}   # score_product يتعامل مع empty dict

        # Filter: لو AI نجح بس رفض المنتج
        if ai.get("is_valid") is False:
            continue
        if ai and ai.get("relevance_score", 1.0) < MIN_RELEVANCE:
            continue
        if ai and ai.get("confidence", 1.0) < MIN_CONFIDENCE:
            continue

        try:
            s = score_product(product, ai)
        except Exception as e:
            logger.warning("Scoring failed for '%s': %s", product.get("title", "")[:30], e)
            continue

        if s.get("profit", 0) < MIN_PROFIT:
            continue

        scored.append(s)

    logger.info("Qualified products: %d", len(scored))

    if not scored:
        return []

    # ── Step 6: Sort ─────────────────────────────────────
    scored.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    top = scored[:TOP_N]

    # ── Step 7: Cache FULL list (not just top 5) ─────────
    # بنحفظ كل الـ scored عشان:
    # - suggestions أفضل
    # - reuse أكتر
    # - filter بالـ verdict بعدين من الـ cache
    try:
        await set_cached(norm, scored)
    except Exception as e:
        logger.warning("Cache write failed: %s", e)

    # ── Step 8: Bulk DB save (مش loop) ───────────────────
    try:
        await save_products_bulk(scored)
        # Price history بـ bulk أيضًا — بسيط
        for item in scored:
            try:
                await record_price(item)
            except Exception:
                pass
    except Exception as e:
        logger.error("Bulk DB save failed: %s", e)

    logger.info("Pipeline done: returning top %d / %d", len(top), len(scored))
    return top


async def run_full_update():
    """Background job: refresh all seed queries."""
    logger.info("Full update started")
    for q in DEFAULT_QUERIES:
        try:
            await run_pipeline(q, force_refresh=True)
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error("Pipeline error for '%s': %s", q, e)

    try:
        await cleanup_old_products()
    except Exception as e:
        logger.error("Cleanup failed: %s", e)

    logger.info("Full update complete")
