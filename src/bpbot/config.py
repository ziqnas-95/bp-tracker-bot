import os
from dataclasses import dataclass
from functools import lru_cache
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

LOCAL_TZ = ZoneInfo("Asia/Kuala_Lumpur")


def _optional(name: str) -> str | None:
    return os.getenv(name, "").strip() or None


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    supabase_url: str
    supabase_service_role_key: str
    allowed_user_id: int
    readings_table: str  # <- new
    webhook_base_url: str | None
    webhook_secret: str | None
    port: int
    family_join_code: str


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing environment variable: {name} (check your .env)")
    return value


@lru_cache
def get_settings() -> Settings:
    # Render sets RENDER_EXTERNAL_URL and PORT automatically
    base_url = _optional("RENDER_EXTERNAL_URL") or _optional("WEBHOOK_BASE_URL")
    secret = _optional("WEBHOOK_SECRET")
    if base_url and not secret:
        raise RuntimeError("WEBHOOK_SECRET is required in webhook mode")

    return Settings(
        telegram_bot_token=_require("TELEGRAM_BOT_TOKEN"),
        supabase_url=_require("SUPABASE_URL"),
        supabase_service_role_key=_require("SUPABASE_SERVICE_ROLE_KEY"),
        allowed_user_id=int(_require("TELEGRAM_ALLOWED_USER_ID")),
        readings_table=_require("READINGS_TABLE"),
        webhook_base_url=base_url.rstrip("/") if base_url else None,
        webhook_secret=secret,
        port=int(os.getenv("PORT", "10000")),
        family_join_code=_require("FAMILY_JOIN_CODE"),
    )
