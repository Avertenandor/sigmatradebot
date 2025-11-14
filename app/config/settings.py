"""
Application settings.

Loads configuration from environment variables using pydantic-settings.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram Bot
    telegram_bot_token: str
    telegram_bot_username: Optional[str] = None

    # Database
    database_url: str
    database_echo: bool = False

    # Admin
    admin_telegram_ids: str = ""  # Comma-separated list

    # Wallet
    wallet_private_key: str
    wallet_address: str
    usdt_contract_address: str
    rpc_url: str

    # Security
    secret_key: str
    encryption_key: str

    # Application
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"

    # Broadcast settings
    broadcast_rate_limit: int = 15  # messages per second
    broadcast_cooldown: int = 900  # 15 minutes in seconds

    # ROI settings
    roi_daily_percent: float = 0.02  # 2% daily
    roi_cap_multiplier: float = 5.0  # 500% cap

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_admin_ids(self) -> list[int]:
        """Parse admin IDs from comma-separated string."""
        if not self.admin_telegram_ids:
            return []
        return [
            int(id_.strip())
            for id_ in self.admin_telegram_ids.split(",")
            if id_.strip()
        ]


# Global settings instance
settings = Settings()
