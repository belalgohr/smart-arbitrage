from fastapi import APIRouter, Query, Request
from backend.services.recommendation_service import get_recommendations, get_trending, get_fresh_picks

router = APIRouter()


@router.get("/recommendations")
async def recommendations(
    request: Request,
    user_id: str = Query("", description="User ID for personalisation"),
    count: int   = Query(5, ge=1, le=20),
):
    """Personalised product recommendations per user (daily seed + diversity)."""
    uid = user_id or (request.client.host if request.client else "anon")
    products = await get_recommendations(user_id=uid, count=count)
    return {"user_id": uid, "total": len(products), "products": products}


@router.get("/trending")
async def trending(limit: int = Query(10, ge=1, le=50)):
    """Global trending products — top BUY deals by score."""
    products = await get_trending(limit)
    return {"total": len(products), "products": products}


@router.get("/new")
async def fresh_picks(limit: int = Query(10, ge=1, le=50)):
    """Freshest BUY products — recently updated."""
    products = await get_fresh_picks(limit)
    return {"total": len(products), "products": products}
