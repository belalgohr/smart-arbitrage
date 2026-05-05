"""
eBay Service
────────────
- Global AsyncClient (مش بنعمله كل request)
- Token caching (مش بنجيب token كل مرة)
- Retry logic (2 attempts لكل fetch)
- Random sleep بين الـ calls
- Safe category parsing
- Mock data لو مفيش API key
"""

import asyncio
import base64
import logging
import random
import time
import uuid
from typing import Dict, List, Optional

import httpx
from backend.core.config import settings

logger = logging.getLogger(__name__)

EBAY_API_BASE = "https://api.ebay.com/buy/browse/v1"
EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"

# ── Global client — مش بنعمله كل request ─────────────────
# بيتعمل مرة واحدة واللي بعدها بيتreuse
_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=15)
    return _client


# ── Token cache ───────────────────────────────────────────
_cached_token: Optional[str] = None
_token_expires_at: float = 0.0


async def _get_token() -> Optional[str]:
    global _cached_token, _token_expires_at

    if _cached_token and time.time() < _token_expires_at:
        return _cached_token

    if not settings.EBAY_APP_ID or not settings.EBAY_CERT_ID:
        return None

    creds = base64.b64encode(
        f"{settings.EBAY_APP_ID}:{settings.EBAY_CERT_ID}".encode()
    ).decode()

    try:
        client = _get_client()
        r = await client.post(
            EBAY_TOKEN_URL,
            headers={
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
        )
        if r.status_code == 200:
            data = r.json()
            _cached_token = data["access_token"]
            _token_expires_at = time.time() + data.get("expires_in", 7200) - 60
            return _cached_token
        logger.warning("eBay token HTTP %d", r.status_code)
    except Exception as e:
        logger.warning("eBay token error: %s", e)
    return None


# ── Single fetch with retry ───────────────────────────────

async def _fetch_one(query: str, limit: int, token: str) -> List[Dict]:
    """Fetch لـ query واحدة — 2 attempts لو فيه error."""
    client = _get_client()
    url = f"{EBAY_API_BASE}/item_summary/search"
    params = {
        "q":      query,
        "limit":  limit,
        "filter": "buyingOptions:{FIXED_PRICE},conditions:{NEW}",
        "sort":   "newlyListed",
    }
    headers = {"Authorization": f"Bearer {token}"}

    for attempt in range(2):
        try:
            r = await client.get(url, headers=headers, params=params)
            if r.status_code == 200:
                return [_normalize(item) for item in r.json().get("itemSummaries", [])]
            logger.warning("eBay HTTP %d for '%s' (attempt %d)", r.status_code, query, attempt + 1)
        except Exception as e:
            logger.warning("eBay fetch error '%s' attempt %d: %s", query, attempt + 1, e)

        if attempt == 0:
            await asyncio.sleep(random.uniform(0.3, 0.7))   # wait قبل retry

    return []


# ── Batch fetch ───────────────────────────────────────────

async def batch_fetch(queries: List[str], limit_per_query: int = 20) -> List[Dict]:
    token = await _get_token()
    if not token:
        logger.warning("No eBay token — using mock data")
        return _mock_batch(queries, limit_per_query)

    sem = asyncio.Semaphore(3)

    async def _one(q):
        async with sem:
            result = await _fetch_one(q, limit_per_query, token)
            await asyncio.sleep(random.uniform(0.2, 0.5))   # random delay بين الـ calls
            return result

    results = await asyncio.gather(*[_one(q) for q in queries], return_exceptions=True)

    all_products, seen_ids = [], set()
    for chunk in results:
        if isinstance(chunk, list):
            for p in chunk:
                if p["id"] not in seen_ids:
                    seen_ids.add(p["id"])
                    all_products.append(p)

    logger.info("eBay batch: %d queries → %d products", len(queries), len(all_products))
    return all_products


async def search_ebay_products(query: str, limit: int = 20) -> List[Dict]:
    return await batch_fetch([query], limit_per_query=limit)


# ── Normalize ─────────────────────────────────────────────

def _normalize(item: Dict) -> Dict:
    price = float(item.get("price", {}).get("value", 0) or 0)

    shipping = 0.0
    opts = item.get("shippingOptions") or []
    if opts:
        shipping = float(opts[0].get("shippingCost", {}).get("value", 0) or 0)

    # Safe category parse — list ممكن تكون فاضية
    cats = item.get("categories") or []
    category = cats[0].get("categoryName", "General") if cats else "General"

    return {
        "id":            item.get("itemId") or str(uuid.uuid4()),
        "title":         item.get("title", ""),
        "image_url":     (item.get("image") or {}).get("imageUrl", ""),
        "ebay_price":    price,
        "shipping_cost": shipping if shipping > 0 else 4.99,
        "reviews_count": int(item.get("feedbackScore") or 0),
        "rating":        _parse_rating(item.get("sellerFeedbackPercentage", "0")),
        "seller_count":  1,
        "ebay_url":      item.get("itemWebUrl", ""),
        "category":      category,
    }


def _parse_rating(pct_str) -> float:
    try:
        return round(float(str(pct_str).replace("%", "")) / 20, 2)
    except Exception:
        return 4.0


# ── Mock data ─────────────────────────────────────────────

MOCK_CATEGORIES = ["Electronics", "Home & Garden", "Sports", "Beauty", "Toys", "Fashion"]


def _mock_batch(queries: List[str], limit: int) -> List[Dict]:
    products = []
    for query in queries:
        for i in range(min(limit, 15)):
            price = round(random.uniform(12, 120), 2)
            products.append({
                "id":            str(uuid.uuid4()),
                "title":         f"{query.title()} - Model {i+1} (Demo)",
                "image_url":     f"https://picsum.photos/seed/{query[:4]}{i}/300/220",
                "ebay_price":    price,
                "shipping_cost": round(random.uniform(2, 8), 2),
                "reviews_count": random.randint(25, 600),
                "rating":        round(random.uniform(3.8, 5.0), 1),
                "seller_count":  random.randint(1, 60),
                "ebay_url":      "https://www.ebay.com",
                "category":      random.choice(MOCK_CATEGORIES),
            })
    return products
