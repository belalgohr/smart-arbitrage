from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # eBay API - اتركه فاضي دلوقتي
    EBAY_APP_ID: str = ""
    EBAY_CERT_ID: str = ""
    EBAY_DEV_ID: str = ""
    EBAY_USER_TOKEN: str = ""

    # Groq AI
    GROQ_API_KEY: str = ""

    # Telegram Bot (اختياري)
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # App Settings
    DB_PATH: str = "arbitrage.db"
    MAX_PRODUCTS: int = 5000
    DATA_TTL_HOURS: int = 48
    UPDATE_INTERVAL_HOURS: int = 6

    # Scoring Weights
    PROFIT_WEIGHT: float = 0.4
    DEMAND_WEIGHT: float = 0.3
    TREND_WEIGHT: float = 0.2
    COMPETITION_WEIGHT: float = 0.1


    # CORS: comma-separated origins or "*" for dev/all
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Admin secret key — set in .env to protect refresh=true
    ADMIN_SECRET: str = ""

    @property
    def origins_list(self) -> list:
        o = self.ALLOWED_ORIGINS.strip()
        if o == "*":
            return ["*"]
        return [x.strip() for x in o.split(",") if x.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

