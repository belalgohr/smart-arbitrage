from fastapi import APIRouter, Query, Path
from backend.services.price_history_service import get_price_history, get_price_trend

router = APIRouter()


@router.get("/price-history/{product_id}")
async def price_history(
    product_id: str = Path(..., description="Product ID"),
    days: int = Query(30, ge=1, le=90, description="How many days back"),
):
    """Return price snapshots for a product over time."""
    history = await get_price_history(product_id, days)
    trend   = await get_price_trend(product_id)
    return {
        "product_id": product_id,
        "days": days,
        "trend": trend,
        "history": history,
    }
