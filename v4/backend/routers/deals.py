from fastapi import APIRouter, Query
from backend.models.product_repo import get_top_deals, get_top_today

router = APIRouter()

@router.get("/deals")
async def get_deals(limit: int = Query(20, le=100)):
    """Get all top BUY deals sorted by score"""
    deals = await get_top_deals(limit)
    return {"total": len(deals), "deals": deals}


@router.get("/top-today")
async def get_top_today_deals(limit: int = Query(10, le=50)):
    """Get today's top deals"""
    deals = await get_top_today(limit)
    return {"total": len(deals), "deals": deals}
