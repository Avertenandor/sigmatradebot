"""
Application settings.

Centralized configuration using Pydantic Settings with env variable loading.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    node_env: str = Field(default="development", alias="NODE_ENV")
    port: int = Field(default=3000, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Telegram Bot
    bot_token: str = Field(..., alias="BOT_TOKEN")
    telegram_webhook_url: Optional[str] = Field(default=None, alias="TELEGRAM_WEBHOOK_URL")
    telegram_webhook_secret: Optional[str] = Field(default=None, alias="TELEGRAM_WEBHOOK_SECRET")

    # Database (PostgreSQL)
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_user: str = Field(default="botuser", alias="DB_USER")
    db_password: str = Field(..., alias="DB_PASSWORD")
    db_name: str = Field(default="sigmatrade", alias="DB_NAME")
    db_logging: bool = Field(default=False, alias="DB_LOGGING")
    db_synchronize: bool = Field(default=False, alias="DB_SYNCHRONIZE")

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_tls: bool = Field(default=False, alias="REDIS_TLS")

    # Blockchain (BSC via QuickNode)
    quicknode_https_url: str = Field(..., alias="QUICKNODE_HTTPS_URL")
    quicknode_wss_url: str = Field(..., alias="QUICKNODE_WSS_URL")
    bsc_chain_id: int = Field(default=56, alias="BSC_CHAIN_ID")
    bsc_network: str = Field(default="mainnet", alias="BSC_NETWORK")

    # Smart Contracts
    usdt_contract_address: str = Field(
        default="0x55d398326f99059fF775485246999027B3197955",
        alias="USDT_CONTRACT_ADDRESS",
    )

    # Wallet Management
    system_wallet_address: str = Field(..., alias="SYSTEM_WALLET_ADDRESS")
    payout_wallet_address: str = Field(..., alias="PAYOUT_WALLET_ADDRESS")
    payout_wallet_private_key: Optional[str] = Field(default=None, alias="PAYOUT_WALLET_PRIVATE_KEY")
    gcp_secret_manager_enabled: bool = Field(default=False, alias="GCP_SECRET_MANAGER_ENABLED")

    # Deposit Tolerance
    deposit_tolerance_mode: str = Field(default="percent", alias="DEPOSIT_TOLERANCE_MODE")
    deposit_tolerance_percent: float = Field(default=0.05, alias="DEPOSIT_TOLERANCE_PERCENT")

    # Deposit Levels (in USDT)
    deposit_level_1: float = Field(default=10.0, alias="DEPOSIT_LEVEL_1")
    deposit_level_2: float = Field(default=50.0, alias="DEPOSIT_LEVEL_2")
    deposit_level_3: float = Field(default=100.0, alias="DEPOSIT_LEVEL_3")
    deposit_level_4: float = Field(default=150.0, alias="DEPOSIT_LEVEL_4")
    deposit_level_5: float = Field(default=300.0, alias="DEPOSIT_LEVEL_5")

    # Referral Commission Rates (as decimals)
    referral_rate_level_1: float = Field(default=0.03, alias="REFERRAL_RATE_LEVEL_1")
    referral_rate_level_2: float = Field(default=0.02, alias="REFERRAL_RATE_LEVEL_2")
    referral_rate_level_3: float = Field(default=0.05, alias="REFERRAL_RATE_LEVEL_3")

    # Security
    jwt_secret: str = Field(default="changeme", alias="JWT_SECRET")
    financial_password_bcrypt_rounds: int = Field(default=12, alias="FINANCIAL_PASSWORD_BCRYPT_ROUNDS")
    session_secret: str = Field(default="changeme", alias="SESSION_SECRET")
    encryption_key: Optional[str] = Field(default=None, alias="ENCRYPTION_KEY")

    # Rate Limiting
    rate_limit_window_ms: int = Field(default=60000, alias="RATE_LIMIT_WINDOW_MS")
    rate_limit_max_requests_per_user: int = Field(default=30, alias="RATE_LIMIT_MAX_REQUESTS_PER_USER")
    rate_limit_max_requests_per_ip: int = Field(default=100, alias="RATE_LIMIT_MAX_REQUESTS_PER_IP")
    rate_limit_ban_duration_ms: int = Field(default=300000, alias="RATE_LIMIT_BAN_DURATION_MS")

    # Blockchain Monitoring
    blockchain_start_block: str = Field(default="latest", alias="BLOCKCHAIN_START_BLOCK")
    blockchain_confirmation_blocks: int = Field(default=12, alias="BLOCKCHAIN_CONFIRMATION_BLOCKS")
    blockchain_poll_interval_ms: int = Field(default=3000, alias="BLOCKCHAIN_POLL_INTERVAL_MS")

    # Background Jobs
    job_blockchain_monitor_enabled: bool = Field(default=True, alias="JOB_BLOCKCHAIN_MONITOR_ENABLED")
    job_payment_processor_enabled: bool = Field(default=True, alias="JOB_PAYMENT_PROCESSOR_ENABLED")
    job_backup_enabled: bool = Field(default=True, alias="JOB_BACKUP_ENABLED")
    job_backup_cron: str = Field(default="0 4 * * *", alias="JOB_BACKUP_CRON")
    job_log_cleanup_cron: str = Field(default="0 3 * * 0", alias="JOB_LOG_CLEANUP_CRON")

    # Backup
    backup_enabled: bool = Field(default=True, alias="BACKUP_ENABLED")
    backup_dir: str = Field(default="./backups", alias="BACKUP_DIR")
    backup_retention_days: int = Field(default=90, alias="BACKUP_RETENTION_DAYS")
    backup_git_remote: str = Field(default="origin", alias="BACKUP_GIT_REMOTE")
    backup_git_branch: str = Field(default="backups/sanitized", alias="BACKUP_GIT_BRANCH")
    backup_keep_days: int = Field(default=3, alias="BACKUP_KEEP_DAYS")
    backup_keep_monthly: int = Field(default=12, alias="BACKUP_KEEP_MONTHLY")
    backup_local_max_gb: int = Field(default=2, alias="BACKUP_LOCAL_MAX_GB")
    gcs_backup_bucket: Optional[str] = Field(default=None, alias="GCS_BACKUP_BUCKET")

    # Disk Management
    disk_watermark_warn: int = Field(default=75, alias="DISK_WATERMARK_WARN")
    disk_watermark_shed: int = Field(default=85, alias="DISK_WATERMARK_SHED")
    disk_watermark_emergency: int = Field(default=92, alias="DISK_WATERMARK_EMERGENCY")

    # Admin
    super_admin_telegram_id: Optional[int] = Field(default=None, alias="SUPER_ADMIN_TELEGRAM_ID")
    admin_telegram_ids: str = Field(default="", alias="ADMIN_TELEGRAM_IDS")
    admin_panel_enabled: bool = Field(default=True, alias="ADMIN_PANEL_ENABLED")

    # Google Cloud
    gcp_project_id: Optional[str] = Field(default=None, alias="GCP_PROJECT_ID")
    gcp_region: str = Field(default="us-central1", alias="GCP_REGION")

    # Monitoring & Alerting
    prometheus_port: int = Field(default=9090, alias="PROMETHEUS_PORT")
    health_check_port: int = Field(default=3000, alias="HEALTH_CHECK_PORT")
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    alert_email: Optional[str] = Field(default=None, alias="ALERT_EMAIL")
    alert_telegram_chat_id: Optional[str] = Field(default=None, alias="ALERT_TELEGRAM_CHAT_ID")

    # Feature Flags
    feature_registration_enabled: bool = Field(default=True, alias="FEATURE_REGISTRATION_ENABLED")
    feature_deposits_enabled: bool = Field(default=True, alias="FEATURE_DEPOSITS_ENABLED")
    feature_withdrawals_enabled: bool = Field(default=True, alias="FEATURE_WITHDRAWALS_ENABLED")
    feature_referrals_enabled: bool = Field(default=True, alias="FEATURE_REFERRALS_ENABLED")
    feature_admin_panel_enabled: bool = Field(default=True, alias="FEATURE_ADMIN_PANEL_ENABLED")

    # Development
    dev_skip_blockchain_verification: bool = Field(default=False, alias="DEV_SKIP_BLOCKCHAIN_VERIFICATION")
    dev_mock_payments: bool = Field(default=False, alias="DEV_MOCK_PAYMENTS")
    dev_reset_db_on_start: bool = Field(default=False, alias="DEV_RESET_DB_ON_START")

    @field_validator("admin_telegram_ids")
    @classmethod
    def parse_admin_ids(cls, v: str) -> str:
        """Validate admin telegram IDs."""
        if not v:
            return v
        # Validate format
        try:
            ids = [int(x.strip()) for x in v.split(",") if x.strip()]
            return ",".join(str(x) for x in ids)
        except ValueError as e:
            raise ValueError(f"Invalid admin_telegram_ids format: {e}")

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.node_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.node_env.lower() == "development"

    @property
    def database_url(self) -> str:
        """Get async PostgreSQL database URL."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        password_part = f":{self.redis_password}@" if self.redis_password else ""
        protocol = "rediss" if self.redis_tls else "redis"
        return f"{protocol}://{password_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def admin_ids_list(self) -> list[int]:
        """Get admin IDs as list."""
        if not self.admin_telegram_ids:
            return []
        return [int(x.strip()) for x in self.admin_telegram_ids.split(",") if x.strip()]

    def get_deposit_level(self, level: int) -> float:
        """
        Get deposit amount for level.

        Args:
            level: Deposit level (1-5)

        Returns:
            Deposit amount in USDT

        Raises:
            ValueError: If invalid level
        """
        if level < 1 or level > 5:
            raise ValueError(f"Invalid deposit level: {level}")

        return getattr(self, f"deposit_level_{level}")

    def get_referral_rate(self, level: int) -> float:
        """
        Get referral commission rate for level.

        Args:
            level: Referral level (1-3)

        Returns:
            Commission rate as decimal (e.g., 0.03 for 3%)

        Raises:
            ValueError: If invalid level
        """
        if level < 1 or level > 3:
            raise ValueError(f"Invalid referral level: {level}")

        return getattr(self, f"referral_rate_level_{level}")


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings singleton.

    Returns:
        Settings instance

    Note:
        Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()
