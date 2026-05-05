import logging
"""
AI Service — Smart Usage
─────────────────────────
- بيستخدم Groq بس لما المنتج جديد (مش موجود في DB)
- نتيجة الـ AI بتتحفظ → مش بنكرر نفس الـ call
- Batch support: 10 منتجات في call واحدة
- Rule-based fallback لو مفيش API key
"""

import httpx
import json
import asyncio
from typing import Dict, Optional, List
from backend.core.config import settings

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"

# ── Prompts ───────────────────────────────────────────────

SINGLE_PROMPT = """\
You are a dropshipping expert. Evaluate this eBay product for resale profitability.

Product:
- Title: {title}
- Category: {category}
- Price: ${price}
- Reviews: {reviews}
- Rating: {rating}/5
- Sellers: {sellers}

Return ONLY valid JSON (no markdown):
{{
  "is_valid": true,
  "relevance_score": 0.92,
  "confidence": 0.88,
  "estimated_cost_ratio": 0.30,
  "demand_signal": "high",
  "risk_flag": "none",
  "reason": "short reason"
}}

Rules:
- is_valid=false if: digital, food, adult, heavy machinery, live animal, requires license
- is_valid=false if title has: lot, bundle, wholesale, broken, parts only, for parts, as is
- relevance_score = resale probability (0-1)
- confidence = certainty (0-1)
- estimated_cost_ratio = AliExpress/eBay ratio (0.15-0.65)
- demand_signal = high|medium|low
- risk_flag = none|high_competition|low_margin|bad_keywords|suspicious
"""

BATCH_PROMPT = """\
You are a dropshipping expert. Evaluate these {count} eBay products for resale.

Products (JSON array):
{products_json}

Return ONLY a JSON array with exactly {count} objects, same order:
[
  {{"is_valid": true, "relevance_score": 0.9, "confidence": 0.85, "estimated_cost_ratio": 0.30, "demand_signal": "high", "risk_flag": "none", "reason": "..."}},
  ...
]

Same rules:
- is_valid=false: digital, food, adult, lot/bundle/wholesale/broken/parts only
- estimated_cost_ratio: 0.15 (very cheap to source) to 0.65 (expensive)
- risk_flag: none|high_competition|low_margin|bad_keywords|suspicious
"""

# ── Pre-filter (بدون AI) ──────────────────────────────────

BAD_KW = [
    "lot of", "bundle", "wholesale", "broken", "parts only", "for parts",
    "untested", "as is", "damaged", "defective", "non working",
    "digital", "subscription", "ebook", "gift card", "pdf",
]
GOOD_KW = [
    "wireless", "bluetooth", "usb", "led", "smart", "portable",
    "electric", "magnetic", "waterproof", "case", "charger",
    "earbuds", "watch", "gadget", "kitchen", "beauty", "fitness",
]


def _pre_filter(product: Dict) -> bool:
    title = product.get("title", "").lower()
    price = product.get("ebay_price", 0)
    if price < 8 or price > 500:
        return False
    if any(kw in title for kw in BAD_KW):
        return False
    return True


# ── Single classify ───────────────────────────────────────

async def classify_product(product: Dict) -> Optional[Dict]:
    """Classify one product — checks pre-filter first."""
    if not _pre_filter(product):
        return None
    if not settings.GROQ_API_KEY:
        return _rule_based(product)
    return await _groq_single(product)


async def _groq_single(product: Dict, retries: int = 2) -> Optional[Dict]:
    prompt = SINGLE_PROMPT.format(
        title    = product.get("title", "")[:180],
        category = product.get("category", "General"),
        price    = product.get("ebay_price", 0),
        reviews  = product.get("reviews_count", 0),
        rating   = product.get("rating", 0),
        sellers  = product.get("seller_count", 1),
    )
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                r = await client.post(
                    GROQ_URL,
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}",
                             "Content-Type": "application/json"},
                    json={"model": GROQ_MODEL,
                          "messages": [{"role": "user", "content": prompt}],
                          "temperature": 0.05, "max_tokens": 220},
                )
            if r.status_code == 429:
                await asyncio.sleep(2 ** attempt)
                continue
            if r.status_code != 200:
                break
            raw = r.json()["choices"][0]["message"]["content"].strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)
            _validate_result(result)
            return result
        except Exception as e:
            logging.getLogger(__name__).warning("Groq error attempt %d: %s", attempt+1, e)
        await asyncio.sleep(1)
    return _rule_based(product)


# ── Batch classify (أهم تحسين للـ API) ───────────────────

async def classify_batch(products: List[Dict], batch_size: int = 10) -> List[Optional[Dict]]:
    """
    بدل ما نبعت كل منتج لوحده:
    نجمع 10 منتجات في prompt واحد → Groq يرد بـ array
    يوفر 90% من الـ API calls
    """
    if not settings.GROQ_API_KEY:
        return [_rule_based(p) if _pre_filter(p) else None for p in products]

    results = [None] * len(products)
    valid_indices = [i for i, p in enumerate(products) if _pre_filter(p)]

    # قسّم على batches من 10
    for start in range(0, len(valid_indices), batch_size):
        chunk_indices = valid_indices[start:start + batch_size]
        chunk = [products[i] for i in chunk_indices]

        batch_results = await _groq_batch(chunk)

        for j, idx in enumerate(chunk_indices):
            if j < len(batch_results):
                results[idx] = batch_results[j]
            else:
                results[idx] = _rule_based(products[idx])

        # delay بين الـ batches
        if start + batch_size < len(valid_indices):
            await asyncio.sleep(0.5)

    return results


async def _groq_batch(products: List[Dict]) -> List[Optional[Dict]]:
    """Groq call لـ batch من المنتجات."""
    products_data = [
        {
            "title":    p.get("title", "")[:100],
            "price":    p.get("ebay_price", 0),
            "reviews":  p.get("reviews_count", 0),
            "rating":   p.get("rating", 0),
            "sellers":  p.get("seller_count", 1),
            "category": p.get("category", "General"),
        }
        for p in products
    ]

    prompt = BATCH_PROMPT.format(
        count=len(products),
        products_json=json.dumps(products_data, ensure_ascii=False)
    )

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            r = await client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}",
                         "Content-Type": "application/json"},
                json={"model": GROQ_MODEL,
                      "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.05, "max_tokens": 1500},
            )

        if r.status_code == 429:
            await asyncio.sleep(3)
            return [_rule_based(p) for p in products]

        if r.status_code != 200:
            return [_rule_based(p) for p in products]

        raw = r.json()["choices"][0]["message"]["content"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        arr = json.loads(raw)

        if not isinstance(arr, list):
            raise ValueError("Expected array")

        validated = []
        for item in arr:
            try:
                _validate_result(item)
                validated.append(item)
            except Exception:
                validated.append(_rule_based(products[len(validated)]))
        return validated

    except Exception as e:
        logging.getLogger(__name__).warning("Groq batch error: %s — using rule-based fallback", e)
        return [_rule_based(p) for p in products]


# ── Rule-based fallback ───────────────────────────────────

def _rule_based(product: Dict) -> Dict:
    price   = product.get("ebay_price", 0)
    reviews = product.get("reviews_count", 0)
    sellers = product.get("seller_count", 1)
    title   = product.get("title", "").lower()

    good_hits = sum(1 for kw in GOOD_KW if kw in title)
    relevance = min(0.70 + good_hits * 0.04, 0.92)
    confidence = 0.72 if reviews > 20 else 0.55

    if price > 80:    cost_ratio = 0.25
    elif price > 30:  cost_ratio = 0.32
    else:             cost_ratio = 0.42

    risk = "none"
    if sellers > 50:                    risk = "high_competition"
    elif price * (1 - cost_ratio) < 5:  risk = "low_margin"

    demand = "high" if reviews > 100 else ("medium" if reviews > 40 else "low")

    return {
        "is_valid":             True,
        "relevance_score":      round(relevance, 3),
        "confidence":           round(confidence, 3),
        "estimated_cost_ratio": cost_ratio,
        "demand_signal":        demand,
        "risk_flag":            risk,
        "reason":               "Rule-based (no Groq key)",
    }


def _validate_result(r: Dict):
    for k in ("is_valid", "relevance_score", "confidence", "estimated_cost_ratio"):
        if k not in r:
            raise ValueError(f"Missing: {k}")
    r["relevance_score"]      = max(0.0, min(1.0, float(r["relevance_score"])))
    r["confidence"]           = max(0.0, min(1.0, float(r["confidence"])))
    r["estimated_cost_ratio"] = max(0.15, min(0.65, float(r["estimated_cost_ratio"])))
