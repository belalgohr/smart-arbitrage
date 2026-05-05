import logging
import httpx
from typing import List, Dict
from backend.core.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API    = "https://api.telegram.org/bot{token}/sendMessage"
REQUEST_TIMEOUT = 10   # seconds — never blocks main flow


async def send_telegram_message(text: str) -> bool:
    """
    Send message to Telegram. Returns True on success.
    Never raises — logs error and returns False on any failure.
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return False

    url = TELEGRAM_API.format(token=settings.TELEGRAM_BOT_TOKEN)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.post(url, json={
                "chat_id":    settings.TELEGRAM_CHAT_ID,
                "text":       text,
                "parse_mode": "HTML",
            })
        if r.status_code == 200:
            return True
        logger.warning("Telegram HTTP %d: %s", r.status_code, r.text[:100])
    except httpx.TimeoutException:
        logger.warning("Telegram request timed out")
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
    return False


async def send_top_deals_alert(deals: List[Dict]) -> bool:
    """Format and send top deals. Returns True if message was sent."""
    if not deals:
        return False

    lines = ["🔥 <b>Top Arbitrage Deals Today</b>\n"]
    for i, deal in enumerate(deals[:5], 1):
        lines.append(
            f"{i}. {deal.get('title', '')[:40]}…\n"
            f"   💰 Profit: <b>${deal.get('profit', 0):.2f}</b> "
            f"| Score: {deal.get('final_score', 0):.2f}\n"
            f"   🔗 <a href='{deal.get('ebay_url', '')}'>View on eBay</a>\n"
        )

    ok = await send_telegram_message("\n".join(lines))
    if ok:
        logger.info("Telegram: sent %d deals", len(deals[:5]))
    return ok
