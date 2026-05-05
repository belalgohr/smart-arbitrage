import logging
import aiosqlite
import hashlib
from typing import Optional, Tuple
from datetime import datetime, timedelta
from backend.core.database import DB_PATH

# ── Config ─────────────────────────────────────────────────
IP_LIMIT_PER_MINUTE   = 20     # max requests per IP per minute
IP_LIMIT_PER_HOUR     = 100    # max requests per IP per hour
SOFT_BLOCK_MINUTES    = 30     # how long a soft block lasts
HARD_BLOCK_HOURS      = 24     # hard block after repeated violations


# ── Fingerprint ────────────────────────────────────────────
def build_fingerprint(ip: str, user_agent: str, accept_lang: str = "") -> str:
    """
    Simple device fingerprint — hash of IP + UA + language.
    Not perfect, but enough to catch trivial evasion.
    """
    raw = f"{ip}|{user_agent}|{accept_lang}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


# ── Block check ────────────────────────────────────────────
async def is_blocked(identifier: str, id_type: str = "ip") -> Tuple[bool, Optional[str]]:
    """
    Returns (blocked: bool, reason: str | None).
    Checks both soft and hard blocks.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT action, blocked_until
            FROM abuse_log
            WHERE identifier = ?
              AND identifier_type = ?
              AND blocked_until IS NOT NULL
              AND datetime(blocked_until) > datetime('now')
            ORDER BY created_at DESC
            LIMIT 1
        """, (identifier, id_type))
        row = await cursor.fetchone()
        if row:
            action, until = row
            return True, f"{action} until {until}"
        return False, None


async def _soft_block(identifier: str, id_type: str, reason: str):
    until = (datetime.utcnow() + timedelta(minutes=SOFT_BLOCK_MINUTES)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO abuse_log (identifier, identifier_type, action, blocked_until)
            VALUES (?, ?, ?, ?)
        """, (identifier, id_type, f"soft_block:{reason}", until))
        await db.commit()


async def _hard_block(identifier: str, id_type: str, reason: str):
    until = (datetime.utcnow() + timedelta(hours=HARD_BLOCK_HOURS)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO abuse_log (identifier, identifier_type, action, blocked_until)
            VALUES (?, ?, ?, ?)
        """, (identifier, id_type, f"hard_block:{reason}", until))
        await db.commit()


# ── Rate limit ─────────────────────────────────────────────
async def check_rate_limit(identifier: str, id_type: str = "ip") -> Tuple[bool, str]:
    """
    Returns (allowed: bool, message: str).
    Applies per-minute + per-hour sliding windows.
    """
    # Already blocked?
    blocked, reason = await is_blocked(identifier, id_type)
    if blocked:
        return False, f"Blocked: {reason}"

    now = datetime.utcnow()
    window_start_minute = (now - timedelta(minutes=1)).isoformat()
    window_start_hour   = (now - timedelta(hours=1)).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        # Count requests in last minute
        cur = await db.execute("""
            SELECT request_count, window_start FROM rate_limit
            WHERE identifier = ? AND identifier_type = ?
        """, (identifier, id_type))
        row = await cur.fetchone()

        if not row:
            # First request — insert
            await db.execute("""
                INSERT INTO rate_limit (identifier, identifier_type, window_start, request_count)
                VALUES (?, ?, ?, 1)
            """, (identifier, id_type, now.isoformat()))
            await db.commit()
            return True, "ok"

        count, win_start = row[0], row[1]

        # Reset window if older than 1 hour
        if win_start < window_start_hour:
            await db.execute("""
                UPDATE rate_limit SET window_start = ?, request_count = 1
                WHERE identifier = ? AND identifier_type = ?
            """, (now.isoformat(), identifier, id_type))
            await db.commit()
            return True, "ok"

        # Increment count
        new_count = count + 1
        await db.execute("""
            UPDATE rate_limit SET request_count = ?
            WHERE identifier = ? AND identifier_type = ?
        """, (new_count, identifier, id_type))
        await db.commit()

        # Per-minute check (approximate via total count / time ratio)
        elapsed_minutes = max((now - datetime.fromisoformat(win_start)).total_seconds() / 60, 0.01)
        rate_per_min = new_count / elapsed_minutes

        if rate_per_min > IP_LIMIT_PER_MINUTE:
            await _soft_block(identifier, id_type, "rate_per_minute")
            return False, "Too many requests per minute. Soft blocked."

        if new_count > IP_LIMIT_PER_HOUR:
            await _hard_block(identifier, id_type, "hourly_limit_exceeded")
            return False, "Hourly limit exceeded. Hard blocked for 24h."

    return True, "ok"


# ── Fingerprint check ──────────────────────────────────────
async def check_fingerprint(fp: str) -> Tuple[bool, str]:
    """Same rate-limit logic applied to device fingerprint."""
    return await check_rate_limit(fp, id_type="fingerprint")


# ── Cleanup ────────────────────────────────────────────────
async def cleanup_expired_blocks():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            DELETE FROM abuse_log
            WHERE blocked_until IS NOT NULL
              AND datetime(blocked_until) <= datetime('now')
        """)
        await db.execute("""
            DELETE FROM rate_limit
            WHERE datetime(window_start) < datetime('now', '-2 hours')
        """)
        await db.commit()
        logging.getLogger(__name__).info("Cleaned %d expired blocks", cursor.rowcount)
