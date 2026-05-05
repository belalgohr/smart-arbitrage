from typing import Dict
from backend.core.config import settings

# ====================================================
# Scoring Engine
# Final Score = (profit*0.4) + (demand*0.3) + (trend*0.2) - (competition*0.1)
# ====================================================

def calculate_profit(product: Dict, cost_ratio: float = 0.35) -> Dict:
    """Calculate actual profit after all fees"""
    sell_price = product.get("ebay_price", 0)
    shipping = product.get("shipping_cost", 5)

    estimated_cost = sell_price * cost_ratio
    ebay_fee = sell_price * 0.13       # eBay ~13% fees
    risk_buffer = 1.0                  # $1 risk buffer
    paypal_fee = sell_price * 0.029 + 0.30  # PayPal fees

    profit = sell_price - estimated_cost - shipping - ebay_fee - risk_buffer - paypal_fee

    return {
        "estimated_cost": round(estimated_cost, 2),
        "profit": round(profit, 2),
        "profit_margin": round((profit / sell_price * 100) if sell_price > 0 else 0, 1)
    }


def calculate_demand_score(reviews: int, rating: float) -> float:
    """Score 0-1 based on reviews and rating"""
    if reviews < 20:
        return 0.0

    # Reviews score (logarithmic)
    import math
    reviews_score = min(math.log(reviews + 1) / math.log(1001), 1.0)

    # Rating score
    rating_score = max(0, (rating - 3.0) / 2.0)

    return round(reviews_score * 0.6 + rating_score * 0.4, 3)


def calculate_competition_score(seller_count: int) -> float:
    """Lower = better (fewer sellers = less competition)"""
    if seller_count <= 5:
        return 0.9
    elif seller_count <= 20:
        return 0.7
    elif seller_count <= 50:
        return 0.4
    else:
        return 0.1


def calculate_trend_score(title: str, category: str) -> float:
    """Simple trend scoring based on keywords - can be replaced with Google Trends API"""
    trending_keywords = [
        "wireless", "bluetooth", "smart", "led", "solar", "portable",
        "mini", "electric", "usb", "magnetic", "foldable", "fast charging",
        "waterproof", "gaming", "rgb", "aesthetic", "vintage"
    ]
    title_lower = title.lower()
    matches = sum(1 for kw in trending_keywords if kw in title_lower)
    base = min(matches * 0.15, 0.8)

    # Category bonus
    hot_categories = ["electronics", "gaming", "sports", "home & garden"]
    if category.lower() in hot_categories:
        base += 0.1

    return min(round(base, 3), 1.0)


def calculate_final_score(profit: float, demand: float, trend: float, competition: float) -> float:
    """
    Final Score = (profit_norm*0.5) + (demand*0.3) + (trend*0.2)
    Competition penalty طفيف مش عامل ضغط كبير.
    """
    # Normalize profit: /30 بدل /50 عشان المنتجات الرخيصة تظهر
    # مثال: profit=$10 → 10/30=0.33 (كان 10/50=0.2 — أضعف)
    profit_norm         = min(max(profit / 30, 0), 1.0)
    competition_penalty = 1 - competition   # أقل sellers = أحسن

    score = (
        profit_norm         * 0.50 +
        demand              * 0.30 +
        trend               * 0.20 -
        competition_penalty * 0.05   # خفيف — مش هيقتل منتجات كويسة
    )
    return round(max(0, min(score, 1.0)), 3)


def get_verdict(score: float, profit: float) -> str:
    """Give clear BUY/SKIP/RISKY verdict"""
    if profit < 2:
        return "SKIP"
    if score >= 0.65:
        return "BUY"
    elif score >= 0.40:
        return "RISKY"
    else:
        return "SKIP"


def score_product(product: Dict, ai_result: Dict) -> Dict:
    """Full scoring pipeline for one product"""
    cost_ratio = ai_result.get("estimated_cost_ratio", 0.35)
    profit_data = calculate_profit(product, cost_ratio)

    demand = calculate_demand_score(
        product.get("reviews_count", 0),
        product.get("rating", 0)
    )
    competition = calculate_competition_score(product.get("seller_count", 1))
    trend = calculate_trend_score(product.get("title", ""), product.get("category", ""))

    final_score = calculate_final_score(
        profit_data["profit"], demand, trend, competition
    )
    verdict = get_verdict(final_score, profit_data["profit"])

    return {
        **product,
        **profit_data,
        "demand_score": demand,
        "competition_score": competition,
        "trend_score": trend,
        "final_score": final_score,
        "verdict": verdict,
        "relevance_score": ai_result.get("relevance_score", 0),
        "confidence": ai_result.get("confidence", 0)
    }
