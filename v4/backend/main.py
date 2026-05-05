import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import search, deals, products, price_history, recommendations

from backend.core.database import init_db, DB_PATH
from backend.core.scheduler import start_scheduler
from backend.core.config import settings


# ── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("aiosqlite").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Smart Arbitrage starting…")
    await init_db()
    asyncio.create_task(start_scheduler())
    logger.info("✅ Ready — origins: %s", settings.origins_list)
    yield
    logger.info("👋 Shutting down")


app = FastAPI(
    title="Smart Arbitrage Finder",
    description="Find profitable dropshipping products automatically",
    version="4.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,   # from .env: ALLOWED_ORIGINS=*
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router,            prefix="/api")
app.include_router(deals.router,             prefix="/api")
app.include_router(products.router,          prefix="/api")
app.include_router(price_history.router,     prefix="/api")
app.include_router(recommendations.router,   prefix="/api")


@app.get("/")
async def root():
    return {"status": "Smart Arbitrage Finder v4 🚀", "docs": "/docs"}


@app.get("/health")
async def health():
    """Real health check — verifies DB is reachable."""
    import aiosqlite
    db_ok = False
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("SELECT 1")
        db_ok = True
    except Exception as e:
        logger.error("Health check DB failed: %s", e)

    status = "ok" if db_ok else "degraded"
    return {
        "status":      status,
        "db":          "ok" if db_ok else "error",
        "cache_ttl_h": 6,
        "version":     "4.0.0",
    }
