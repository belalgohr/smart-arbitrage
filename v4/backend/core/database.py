import logging
import aiosqlite

# ── Single source of truth للـ DB_PATH ──────────────────
# كل الملفات بتعمل `from routers.database import DB_PATH`
# فبدل ما نغيّرهم كلهم، خلّي database.py نفسه يقرأ من settings
from backend.core.config import settings
DB_PATH = settings.DB_PATH

# ═══════════════════════════════════════════════════
# TABLE DEFINITIONS  (كلها فوق init_db عشان مفيش NameError)
# ═══════════════════════════════════════════════════

CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    id                TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    image_url         TEXT,
    ebay_price        REAL,
    estimated_cost    REAL,
    shipping_cost     REAL,
    profit            REAL,
    profit_margin     REAL,
    demand_score      REAL,
    trend_score       REAL,
    competition_score REAL,
    final_score       REAL,
    reviews_count     INTEGER,
    rating            REAL,
    seller_count      INTEGER,
    category          TEXT,
    relevance_score   REAL,
    risk_flag         TEXT DEFAULT 'none',
    verdict           TEXT,
    ebay_url          TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PRICE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS price_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id     TEXT NOT NULL,
    product_title  TEXT,
    ebay_price     REAL,
    estimated_cost REAL,
    profit         REAL,
    final_score    REAL,
    verdict        TEXT,
    recorded_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_SEARCH_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS search_cache (
    query         TEXT PRIMARY KEY,
    results       TEXT NOT NULL,
    product_count INTEGER DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_RATE_LIMIT_TABLE = """
CREATE TABLE IF NOT EXISTS rate_limit (
    identifier      TEXT NOT NULL,
    identifier_type TEXT NOT NULL,
    window_start    TIMESTAMP NOT NULL,
    request_count   INTEGER DEFAULT 1,
    PRIMARY KEY (identifier, identifier_type)
);
"""

CREATE_ABUSE_TABLE = """
CREATE TABLE IF NOT EXISTS abuse_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier      TEXT NOT NULL,
    identifier_type TEXT NOT NULL,
    action          TEXT NOT NULL,
    blocked_until   TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS alerts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT,
    message    TEXT,
    sent_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# ── تتبع بحث المستخدمين (للـ suggestions + limits) ──────
CREATE_USER_SEARCHES_TABLE = """
CREATE TABLE IF NOT EXISTS user_searches (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT NOT NULL,
    query        TEXT NOT NULL,
    result_count INTEGER DEFAULT 0,
    searched_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# ═══════════════════════════════════════════════════
# INIT
# ═══════════════════════════════════════════════════

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        for sql in [
            CREATE_PRODUCTS_TABLE,
            CREATE_PRICE_HISTORY_TABLE,
            "CREATE INDEX IF NOT EXISTS idx_ph_product ON price_history(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_ph_time    ON price_history(recorded_at);",
            CREATE_SEARCH_CACHE_TABLE,
            CREATE_RATE_LIMIT_TABLE,
            CREATE_ABUSE_TABLE,
            "CREATE INDEX IF NOT EXISTS idx_abuse_id ON abuse_log(identifier, identifier_type);",
            CREATE_ALERTS_TABLE,
            CREATE_USER_SEARCHES_TABLE,
            "CREATE INDEX IF NOT EXISTS idx_us_user    ON user_searches(user_id, searched_at);",
            # ── Performance index على title للـ LIKE search ──
            "CREATE INDEX IF NOT EXISTS idx_prod_title ON products(title);",
            "CREATE INDEX IF NOT EXISTS idx_prod_score ON products(final_score DESC);",
            "CREATE INDEX IF NOT EXISTS idx_prod_verdict ON products(verdict);",
        ]:
            await db.execute(sql)
        await db.commit()
    logging.getLogger(__name__).info("Database initialized")


async def get_db():
    return await aiosqlite.connect(DB_PATH)
