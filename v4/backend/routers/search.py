"""
Search Router — Refactored
───────────────────────────
Flow per request:
  1. IP rate-limit check
  2. User daily limit check
  3. Cache check  ← رجّع فوراً لو موجود
  4. لو مفيش cache → pipeline (sync، مش background)
  5. Record search
  6. Return top 5
"""

from fastapi import APIRouter, Query, Request, HTTPException
from backend.services.pipeline            import run_pipeline
from backend.services.cache_service       import find_similar_cached, get_cache_stats, normalize_query
from backend.services.abuse_service       import check_rate_limit, build_fingerprint
from backend.services.user_limits_service import can_search, record_search, get_popular_searches, get_user_history
from backend.models.product_repo          import get_stats
from backend.core.config                  import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_QUERY_LEN = 100   # حماية من spam/garbage queries


def _get_ip(request: Request) -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    return fwd.split(",")[0].strip() or (request.client.host if request.client else "0.0.0.0")


def _get_uid(request: Request, user_id: str) -> str:
    return user_id.strip() or _get_ip(request)


def _is_admin(request: Request) -> bool:
    """Simple admin check via header or query param."""
    if not settings.ADMIN_SECRET:
        return False   # لو مفيش secret → مفيش admin
    header = request.headers.get("X-Admin-Secret", "")
    return header == settings.ADMIN_SECRET


@router.get("/search")
async def search_products(
    request:  Request,
    q:        str  = Query(..., min_length=1, description="Search keyword"),
    verdict:  str  = Query("", description="Filter: BUY | RISKY | SKIP"),
    refresh:  bool = Query(False, description="Force bypass cache"),
    user_id:  str  = Query("", description="User ID"),
):
    # ── 1) Query validation ──────────────────────────────
    q = q.strip()
    if len(q) > MAX_QUERY_LEN:
        raise HTTPException(400, f"Query too long (max {MAX_QUERY_LEN} chars)")

    # ── 2) Refresh protection — admin only ───────────────
    if refresh and not _is_admin(request):
        raise HTTPException(403, "refresh=true requires admin access")

    # ── 3) IP abuse check ────────────────────────────────
    ip = _get_ip(request)
    ua = request.headers.get("user-agent", "")
    fp = build_fingerprint(ip, ua)

    ok_ip, msg_ip = await check_rate_limit(ip, "ip")
    if not ok_ip:
        raise HTTPException(429, detail=msg_ip)

    ok_fp, msg_fp = await check_rate_limit(fp, "fingerprint")
    if not ok_fp:
        raise HTTPException(429, detail=msg_fp)

    # ── 4) User daily limit ──────────────────────────────
    uid = _get_uid(request, user_id)
    ok_user, limit_msg = await can_search(uid)
    if not ok_user:
        raise HTTPException(429, detail=limit_msg)

    # ── 5) Cache check ───────────────────────────────────
    norm = normalize_query(q)

    if not refresh:
        cached = await find_similar_cached(norm)
        if cached is not None:
            filtered = [p for p in cached if not verdict or p.get("verdict") == verdict.upper()]
            await record_search(uid, norm, len(filtered))
            return {
                "query":      q,
                "source":     "cache",
                "total":      len(filtered),
                "products":   filtered[:5],
                "limit_info": limit_msg,
                "refreshing": False,
            }

    # ── 6) Pipeline — wrapped in try/except ──────────────
    try:
        products = await run_pipeline(norm, force_refresh=refresh)
    except Exception as e:
        logger.error("Pipeline failed for '%s': %s", norm, e)
        raise HTTPException(500, "Search failed — please try again")

    if verdict:
        products = [p for p in products if p.get("verdict") == verdict.upper()]

    await record_search(uid, norm, len(products))

    return {
        "query":      q,
        "source":     "fresh",
        "total":      len(products),
        "products":   products[:5],
        "limit_info": limit_msg,
        "refreshing": False,
    }


@router.get("/stats")
async def overview_stats():
    stats = await get_stats()
    cache = await get_cache_stats()
    return {**stats, "cache": cache}


@router.get("/suggestions")
async def suggestions(limit: int = Query(8, le=20)):
    """Popular searches — reused from DB, zero extra API calls."""
    popular = await get_popular_searches(limit)
    return {"suggestions": popular}


@router.get("/history")
async def user_history(
    request:  Request,
    user_id:  str = Query(""),
    limit:    int = Query(10, le=30),
):
    uid = _get_uid(request, user_id)
    history = await get_user_history(uid, limit)
    return {"user_id": uid, "history": history}
