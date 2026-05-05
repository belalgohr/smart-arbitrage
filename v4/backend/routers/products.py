from fastapi import APIRouter, BackgroundTasks, Query
from backend.services.pipeline import run_pipeline, run_full_update, DEFAULT_QUERIES
from backend.models.product_repo import get_products
from backend.services.cache_service import cleanup_stale_cache

router = APIRouter()


@router.post("/products/refresh")
async def refresh_products(
    background_tasks: BackgroundTasks,
    query: str = Query("", description="Specific query or empty for full update"),
):
    if query:
        background_tasks.add_task(run_pipeline, query, 30, True)
        return {"message": f"Refreshing: '{query}'"}
    else:
        background_tasks.add_task(run_full_update)
        return {"message": "Full update started in background"}


@router.get("/products")
async def list_products(
    verdict: str = Query(""),
    limit:   int = Query(50, le=200),
    offset:  int = Query(0),
):
    products = await get_products(verdict=verdict, limit=limit, offset=offset)
    return {"total": len(products), "products": products}


@router.get("/categories")
async def get_seed_queries():
    return {"queries": DEFAULT_QUERIES}


@router.post("/cache/cleanup")
async def cleanup_cache():
    await cleanup_stale_cache()
    return {"message": "Cache cleaned"}
