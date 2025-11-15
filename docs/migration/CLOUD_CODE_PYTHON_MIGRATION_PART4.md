# 🐍 ТЕХНИЧЕСКОЕ ЗАДАНИЕ: Миграция на Python - ЧАСТЬ 4 (КРИТИЧНЫЕ ДЕТАЛИ)

**Продолжение ЧАСТИ 3 - ОБЯЗАТЕЛЬНЫЕ компоненты для полноценной работы**

---

## 🛠️ МОДУЛЬ 16: Utils - Formatters (ПОЛНАЯ РЕАЛИЗАЦИЯ)

### Файл: `app/utils/formatting.py`

```python
"""Text formatting utilities."""
from decimal import Decimal
from datetime import datetime
from typing import Optional


def format_amount(
    amount: Decimal,
    currency: str = "BNB",
    precision: int = 8
) -> str:
    """
    Форматирование суммы.
    
    Args:
        amount: Сумма
        currency: Валюта
        precision: Точность
        
    Returns:
        Форматированная строка
        
    Examples:
        >>> format_amount(Decimal("0.12345678"))
        "0.12345678 BNB"
        >>> format_amount(Decimal("1.5"), precision=2)
        "1.50 BNB"
    """
    format_str = f"{{:.{precision}f}}"
    return f"{format_str.format(amount)} {currency}"


def format_large_number(number: int) -> str:
    """
    Форматирование больших чисел.
    
    Args:
        number: Число
        
    Returns:
        Форматированная строка
        
    Examples:
        >>> format_large_number(1234567)
        "1,234,567"
    """
    return f"{number:,}"


def format_percentage(
    value: float,
    precision: int = 2
) -> str:
    """
    Форматирование процентов.
    
    Args:
        value: Значение (0.05 = 5%)
        precision: Точность
        
    Returns:
        Форматированная строка
        
    Examples:
        >>> format_percentage(0.05)
        "5.00%"
    """
    percentage = value * 100
    return f"{percentage:.{precision}f}%"


def truncate_text(
    text: str,
    max_length: int = 50,
    suffix: str = "..."
) -> str:
    """
    Обрезка текста.
    
    Args:
        text: Текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста
        
    Returns:
        Обрезанный текст
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_address(address: str, start: int = 6, end: int = 4) -> str:
    """
    Форматирование адреса кошелька.
    
    Args:
        address: Адрес
        start: Символов в начале
        end: Символов в конце
        
    Returns:
        Форматированный адрес
        
    Examples:
        >>> format_address("0x1234567890abcdef1234567890abcdef12345678")
        "0x1234...5678"
    """
    if len(address) <= start + end:
        return address
    return f"{address[:start]}...{address[-end:]}"


def format_duration(seconds: int) -> str:
    """
    Форматирование длительности.
    
    Args:
        seconds: Секунды
        
    Returns:
        Человекочитаемая строка
        
    Examples:
        >>> format_duration(3661)
        "1ч 1м 1с"
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}ч")
    if minutes > 0:
        parts.append(f"{minutes}м")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}с")
    
    return " ".join(parts)
```

### Файл: `app/utils/datetime_helpers.py`

```python
"""DateTime utilities."""
from datetime import datetime, timedelta
from typing import Optional
import pytz


def utc_now() -> datetime:
    """
    Текущее UTC время.
    
    Returns:
        Datetime в UTC
    """
    return datetime.now(pytz.UTC)


def to_utc(dt: datetime) -> datetime:
    """
    Конвертация в UTC.
    
    Args:
        dt: Datetime
        
    Returns:
        Datetime в UTC
    """
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(pytz.UTC)


def format_datetime(
    dt: datetime,
    format_str: str = "%d.%m.%Y %H:%M"
) -> str:
    """
    Форматирование datetime.
    
    Args:
        dt: Datetime
        format_str: Формат
        
    Returns:
        Форматированная строка
    """
    return dt.strftime(format_str)


def format_relative_time(dt: datetime) -> str:
    """
    Форматирование относительного времени.
    
    Args:
        dt: Datetime
        
    Returns:
        Человекочитаемая строка
        
    Examples:
        >>> format_relative_time(utc_now() - timedelta(minutes=5))
        "5 минут назад"
    """
    now = utc_now()
    diff = now - dt
    
    seconds = int(diff.total_seconds())
    
    if seconds < 60:
        return "только что"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} минут назад"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} часов назад"
    elif seconds < 604800:
        days = seconds // 86400
        return f"{days} дней назад"
    else:
        weeks = seconds // 604800
        return f"{weeks} недель назад"


def is_expired(dt: datetime, duration: timedelta) -> bool:
    """
    Проверка истечения срока.
    
    Args:
        dt: Datetime
        duration: Длительность
        
    Returns:
        True если истек
    """
    return utc_now() > dt + duration
```

---

## 📊 МОДУЛЬ 17: Constants и Enums (ПОЛНАЯ РЕАЛИЗАЦИЯ)

### Файл: `app/utils/constants.py`

```python
"""Application constants."""
from decimal import Decimal


# Blockchain
BSC_CHAIN_ID = 56
BNB_DECIMALS = 18
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# Confirmations
REQUIRED_CONFIRMATIONS = 12
CONFIRMATIONS_CHECK_INTERVAL = 30  # seconds

# Amounts
MIN_DEPOSIT_AMOUNT = Decimal("0.01")
MAX_DEPOSIT_AMOUNT = Decimal("100")
MIN_WITHDRAWAL_AMOUNT = Decimal("0.01")
MAX_WITHDRAWAL_AMOUNT = Decimal("100")

# Fees
WITHDRAWAL_FEE_PERCENT = Decimal("0.02")  # 2%
MIN_WITHDRAWAL_FEE = Decimal("0.001")

# Referral
REFERRAL_LEVELS = 3
REFERRAL_REWARDS = [
    Decimal("0.05"),  # 5% Level 1
    Decimal("0.03"),  # 3% Level 2
    Decimal("0.02"),  # 2% Level 3
]

# ROI
DEFAULT_ROI_PERCENT = Decimal("0.01")  # 1% daily
ROI_PAYOUT_HOUR = 0  # 00:00 UTC

# Rate Limiting
RATE_LIMIT_PER_MINUTE = 20
RATE_LIMIT_WINDOW = 60  # seconds

# Retry
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 2  # seconds
RETRY_BACKOFF_MAX = 300  # seconds

# Dead Letter Queue
DLQ_MAX_AGE_DAYS = 7
DLQ_CLEANUP_HOUR = 3  # 03:00 UTC

# Support
MAX_OPEN_TICKETS_PER_USER = 5
TICKET_AUTO_CLOSE_DAYS = 30

# Admin
MAX_BROADCAST_BATCH = 100
BROADCAST_DELAY_MS = 50

# Session
SESSION_EXPIRE_HOURS = 24
ADMIN_SESSION_EXPIRE_HOURS = 8

# Finpass
FINPASS_MAX_ATTEMPTS = 3
FINPASS_LOCK_DURATION_MINUTES = 30

# Pagination
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# Disk Guard
DISK_WARNING_PERCENT = 80
DISK_CRITICAL_PERCENT = 90
DISK_CHECK_INTERVAL = 300  # seconds

# Logging
LOG_RETENTION_DAYS = 30
LOG_MAX_SIZE_MB = 100

# Cache
CACHE_USER_TTL = 300  # 5 minutes
CACHE_SETTINGS_TTL = 600  # 10 minutes
CACHE_STATS_TTL = 60  # 1 minute
```

### Файл: `app/utils/enums.py`

```python
"""Application enums."""
from enum import Enum


class UserRole(str, Enum):
    """Роли пользователей."""
    
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class DepositStatus(str, Enum):
    """Статусы депозита."""
    
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WithdrawalStatus(str, Enum):
    """Статусы вывода."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransactionType(str, Enum):
    """Типы транзакций."""
    
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    REFERRAL_REWARD = "referral_reward"
    ROI_PAYOUT = "roi_payout"
    BONUS = "bonus"
    PENALTY = "penalty"
    ADJUSTMENT = "adjustment"


class NotificationType(str, Enum):
    """Типы уведомлений."""
    
    DEPOSIT_CONFIRMED = "deposit_confirmed"
    WITHDRAWAL_COMPLETED = "withdrawal_completed"
    REFERRAL_REWARD = "referral_reward"
    ROI_PAYOUT = "roi_payout"
    TICKET_REPLY = "ticket_reply"
    ADMIN_MESSAGE = "admin_message"
    SYSTEM = "system"


class TicketStatus(str, Enum):
    """Статусы тикета."""
    
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_USER = "waiting_user"
    WAITING_ADMIN = "waiting_admin"
    CLOSED = "closed"


class TicketCategory(str, Enum):
    """Категории тикетов."""
    
    FINANCE = "finance"
    TECHNICAL = "technical"
    REFERRAL = "referral"
    OTHER = "other"


class SenderType(str, Enum):
    """Типы отправителей сообщений."""
    
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"


class AuditAction(str, Enum):
    """Типы аудит действий."""
    
    USER_REGISTERED = "user_registered"
    USER_BANNED = "user_banned"
    USER_UNBANNED = "user_unbanned"
    BALANCE_ADJUSTED = "balance_adjusted"
    DEPOSIT_CREATED = "deposit_created"
    DEPOSIT_CONFIRMED = "deposit_confirmed"
    WITHDRAWAL_CREATED = "withdrawal_created"
    WITHDRAWAL_PROCESSED = "withdrawal_processed"
    SETTINGS_CHANGED = "settings_changed"
    BROADCAST_SENT = "broadcast_sent"
    FINPASS_CHANGED = "finpass_changed"
    FINPASS_LOCKED = "finpass_locked"


class ROIStatus(str, Enum):
    """Статусы ROI."""
    
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SettingType(str, Enum):
    """Типы настроек."""
    
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    JSON = "json"
```

---

## ✅ МОДУЛЬ 18: Validators (ПОЛНАЯ РЕАЛИЗАЦИЯ)

### Файл: `app/utils/validation.py`

```python
"""Validation utilities."""
import re
from decimal import Decimal, InvalidOperation
from typing import Optional
from web3 import Web3

from app.utils.constants import (
    MIN_DEPOSIT_AMOUNT,
    MAX_DEPOSIT_AMOUNT,
    MIN_WITHDRAWAL_AMOUNT,
    MAX_WITHDRAWAL_AMOUNT
)


def validate_ethereum_address(address: str) -> bool:
    """
    Валидация Ethereum/BSC адреса.
    
    Args:
        address: Адрес
        
    Returns:
        True если валидный
        
    Examples:
        >>> validate_ethereum_address("0x1234...") 
        True
        >>> validate_ethereum_address("invalid")
        False
    """
    if not address or not isinstance(address, str):
        return False
    
    # Проверка формата
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        return False
    
    # Проверка checksum
    try:
        return Web3.is_checksum_address(address)
    except Exception:
        return False


def validate_amount(
    amount: str | Decimal,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None
) -> tuple[bool, Optional[str]]:
    """
    Валидация суммы.
    
    Args:
        amount: Сумма
        min_amount: Минимальная сумма
        max_amount: Максимальная сумма
        
    Returns:
        (is_valid, error_message)
        
    Examples:
        >>> validate_amount("0.5", Decimal("0.1"), Decimal("1"))
        (True, None)
        >>> validate_amount("0.05", Decimal("0.1"), Decimal("1"))
        (False, "Сумма меньше минимальной")
    """
    try:
        amount_decimal = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        return False, "Неверный формат суммы"
    
    if amount_decimal <= 0:
        return False, "Сумма должна быть больше 0"
    
    if min_amount and amount_decimal < min_amount:
        return False, f"Минимальная сумма: {min_amount}"
    
    if max_amount and amount_decimal > max_amount:
        return False, f"Максимальная сумма: {max_amount}"
    
    return True, None


def validate_deposit_amount(amount: str | Decimal) -> tuple[bool, Optional[str]]:
    """
    Валидация суммы депозита.
    
    Args:
        amount: Сумма
        
    Returns:
        (is_valid, error_message)
    """
    return validate_amount(
        amount,
        MIN_DEPOSIT_AMOUNT,
        MAX_DEPOSIT_AMOUNT
    )


def validate_withdrawal_amount(
    amount: str | Decimal,
    balance: Decimal
) -> tuple[bool, Optional[str]]:
    """
    Валидация суммы вывода.
    
    Args:
        amount: Сумма
        balance: Баланс пользователя
        
    Returns:
        (is_valid, error_message)
    """
    is_valid, error = validate_amount(
        amount,
        MIN_WITHDRAWAL_AMOUNT,
        MAX_WITHDRAWAL_AMOUNT
    )
    
    if not is_valid:
        return False, error
    
    amount_decimal = Decimal(str(amount))
    
    if amount_decimal > balance:
        return False, "Недостаточно средств"
    
    return True, None


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Валидация username.
    
    Args:
        username: Username
        
    Returns:
        (is_valid, error_message)
    """
    if not username:
        return True, None  # Username опционален
    
    if len(username) < 3:
        return False, "Минимум 3 символа"
    
    if len(username) > 32:
        return False, "Максимум 32 символа"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Только буквы, цифры и _"
    
    return True, None


def validate_financial_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Валидация финансового пароля.
    
    Args:
        password: Пароль
        
    Returns:
        (is_valid, error_message)
    """
    if not password:
        return False, "Пароль не может быть пустым"
    
    if len(password) < 4:
        return False, "Минимум 4 символа"
    
    if len(password) > 32:
        return False, "Максимум 32 символа"
    
    if not re.match(r'^[0-9]+$', password):
        return False, "Только цифры"
    
    return True, None


def validate_transaction_hash(tx_hash: str) -> bool:
    """
    Валидация transaction hash.
    
    Args:
        tx_hash: Transaction hash
        
    Returns:
        True если валидный
    """
    if not tx_hash:
        return False
    
    return bool(re.match(r'^0x[a-fA-F0-9]{64}$', tx_hash))
```

---

## 🔐 МОДУЛЬ 19: Encryption (ПОЛНАЯ РЕАЛИЗАЦИЯ)

### Файл: `app/services/security/encryption.py`

```python
"""Encryption utilities."""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64

from app.core.config import settings


class EncryptionService:
    """Сервис шифрования."""
    
    def __init__(self) -> None:
        """Инициализация с ключом из настроек."""
        self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())
    
    def encrypt(self, data: str) -> str:
        """
        Шифрование данных.
        
        Args:
            data: Данные для шифрования
            
        Returns:
            Зашифрованная строка (base64)
        """
        encrypted = self.fernet.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Расшифровка данных.
        
        Args:
            encrypted_data: Зашифрованные данные
            
        Returns:
            Расшифрованная строка
        """
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted = self.fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    
    @staticmethod
    def generate_key() -> str:
        """
        Генерация нового ключа шифрования.
        
        Returns:
            Base64 ключ
        """
        return Fernet.generate_key().decode()
    
    @staticmethod
    def hash_password(password: str, salt: bytes) -> str:
        """
        Хеширование пароля с солью.
        
        Args:
            password: Пароль
            salt: Соль
            
        Returns:
            Хеш (base64)
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = kdf.derive(password.encode())
        return base64.b64encode(key).decode()
    
    @staticmethod
    def generate_salt() -> bytes:
        """
        Генерация соли.
        
        Returns:
            Случайная соль
        """
        import os
        return os.urandom(16)
```

---

## 📝 МОДУЛЬ 20: Alembic Setup (ПОЛНАЯ РЕАЛИЗАЦИЯ)

### Файл: `alembic.ini`

```ini
[alembic]
script_location = app/database/migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = 

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### Файл: `app/database/migrations/env.py`

```python
"""Alembic environment."""
from logging.config import fileConfig
import asyncio

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.models.base import Base

# Import all models
from app.models import (
    user, deposit, withdrawal, transaction,
    referral, reward, notification, support,
    admin, settings as settings_model, wallet,
    payment, audit, broadcast, finpass, roi
)

# Alembic Config
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata

# Set database URL from settings
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("+asyncpg", "")
)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    Generates SQL scripts without DB connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with connection.
    
    Args:
        connection: Database connection
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Создание первой миграции:

```bash
# Команда для создания
alembic revision --autogenerate -m "Initial schema"

# Применение миграций
alembic upgrade head

# Откат миграций
alembic downgrade -1
```

---

## 📊 МОДУЛЬ 21: Logging Setup (ПОЛНАЯ РЕАЛИЗАЦИЯ)

### Файл: `app/core/logging.py`

```python
"""Logging configuration."""
import sys
from pathlib import Path
from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """
    Настройка системы логирования.
    
    Конфигурирует loguru для вывода в:
    - Console (stderr)
    - Файл app.log (ротация по размеру)
    - Файл errors.log (только ошибки)
    """
    # Удаление дефолтного handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:"
            "<cyan>{line}</cyan> - <level>{message}</level>"
        ),
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # Создание директории для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # App log (все уровни)
    logger.add(
        log_dir / "app.log",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} - {message}"
        ),
        level="DEBUG",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        enqueue=True
    )
    
    # Error log (только ошибки)
    logger.add(
        log_dir / "errors.log",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} - {message}\n{exception}"
        ),
        level="ERROR",
        rotation="50 MB",
        retention="60 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True
    )
    
    logger.info("Logging configured successfully")


# Функция для получения логгера с контекстом
def get_logger(name: str):
    """
    Получить logger с именем модуля.
    
    Args:
        name: Имя модуля
        
    Returns:
        Logger instance
        
    Example:
        >>> from app.core.logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Message")
    """
    return logger.bind(name=name)
```

---

## 🏥 МОДУЛЬ 22: Health Checks (ПОЛНАЯ РЕАЛИЗАЦИЯ)

### Файл: `app/core/health.py`

```python
"""Health check utilities."""
from typing import Dict, Any
from loguru import logger

from app.database.session import async_session_maker
from app.core.config import settings
import aiohttp
import redis.asyncio as aioredis


async def check_database() -> Dict[str, Any]:
    """
    Проверка подключения к БД.
    
    Returns:
        Статус и информация
    """
    try:
        async with async_session_maker() as session:
            await session.execute("SELECT 1")
            return {
                "status": "healthy",
                "message": "Database connection OK"
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }


async def check_redis() -> Dict[str, Any]:
    """
    Проверка подключения к Redis.
    
    Returns:
        Статус и информация
    """
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        await redis_client.close()
        return {
            "status": "healthy",
            "message": "Redis connection OK"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}"
        }


async def check_blockchain() -> Dict[str, Any]:
    """
    Проверка подключения к blockchain RPC.
    
    Returns:
        Статус и информация
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                settings.QUICKNODE_HTTP_URL,
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    block_number = int(data["result"], 16)
                    return {
                        "status": "healthy",
                        "message": "Blockchain RPC OK",
                        "block_number": block_number
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"RPC returned {response.status}"
                    }
    except Exception as e:
        logger.error(f"Blockchain health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Blockchain error: {str(e)}"
        }


async def health_check() -> Dict[str, Any]:
    """
    Полная проверка здоровья системы.
    
    Returns:
        Словарь со статусами всех компонентов
    """
    logger.info("Running health checks...")
    
    results = {
        "database": await check_database(),
        "redis": await check_redis(),
        "blockchain": await check_blockchain(),
    }
    
    # Общий статус
    all_healthy = all(
        component["status"] == "healthy" 
        for component in results.values()
    )
    
    results["overall"] = {
        "status": "healthy" if all_healthy else "unhealthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }
    
    logger.info(f"Health check complete: {results['overall']['status']}")
    
    return results
```

---

## 🔄 МОДУЛЬ 23: Graceful Shutdown (КРИТИЧНО!)

### Файл: `app/core/shutdown.py`

```python
"""Graceful shutdown handler."""
import signal
import asyncio
from typing import Optional
from loguru import logger


class GracefulShutdown:
    """
    Обработчик graceful shutdown.
    
    Гарантирует корректное завершение всех процессов.
    """
    
    def __init__(self) -> None:
        self.shutdown_event = asyncio.Event()
        self.tasks: list[asyncio.Task] = []
    
    def register_task(self, task: asyncio.Task) -> None:
        """
        Регистрация задачи для отслеживания.
        
        Args:
            task: Asyncio task
        """
        self.tasks.append(task)
    
    async def shutdown(self, signal_received: Optional[int] = None) -> None:
        """
        Выполнение shutdown.
        
        Args:
            signal_received: Полученный сигнал
        """
        if signal_received:
            logger.warning(
                f"Received signal {signal_received}, "
                "initiating graceful shutdown..."
            )
        else:
            logger.info("Initiating graceful shutdown...")
        
        # Установка флага shutdown
        self.shutdown_event.set()
        
        # Отмена всех задач
        logger.info(f"Cancelling {len(self.tasks)} tasks...")
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Ожидание завершения задач
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("Graceful shutdown complete")
    
    def setup_signal_handlers(self) -> None:
        """Настройка обработчиков сигналов."""
        loop = asyncio.get_event_loop()
        
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self.shutdown(s))
            )
        
        logger.info("Signal handlers configured")
```

---

## 📊 МОДУЛЬ 24: Performance Monitoring (ПОЛНАЯ РЕАЛИЗАЦИЯ)

### Файл: `app/core/monitoring.py`

```python
"""Performance monitoring utilities."""
import time
import functools
from typing import Callable, Any
from loguru import logger
import psutil
from datetime import datetime


class PerformanceMonitor:
    """Мониторинг производительности."""
    
    @staticmethod
    def get_system_metrics() -> dict[str, Any]:
        """
        Получение системных метрик.
        
        Returns:
            Словарь с метриками
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total_gb": round(memory.total / 1024**3, 2),
                "used_gb": round(memory.used / 1024**3, 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / 1024**3, 2),
                "used_gb": round(disk.used / 1024**3, 2),
                "percent": disk.percent
            }
        }
    
    @staticmethod
    def measure_time(func: Callable) -> Callable:
        """
        Декоратор для измерения времени выполнения.
        
        Args:
            func: Функция для измерения
            
        Returns:
            Обернутая функция
            
        Example:
            >>> @PerformanceMonitor.measure_time
            >>> async def slow_function():
            >>>     await asyncio.sleep(1)
        """
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(
                    f"{func.__name__} took {elapsed:.3f}s"
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {elapsed:.3f}s: {e}"
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(
                    f"{func.__name__} took {elapsed:.3f}s"
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {elapsed:.3f}s: {e}"
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
```

---

## 💾 МОДУЛЬ 25: Backup Scripts (ПОЛНАЯ РЕАЛИЗАЦИЯ)

### Файл: `scripts/backup.py`

```python
"""Database backup script."""
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from loguru import logger

from app.core.config import settings


async def backup_database() -> None:
    """
    Создание backup базы данных.
    
    Использует pg_dump для создания полного backup.
    """
    logger.info("Starting database backup...")
    
    # Создание директории для backups
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    # Имя файла с timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"backup_{timestamp}.sql"
    
    # Команда pg_dump
    command = [
        "pg_dump",
        "-h", settings.DB_HOST,
        "-p", str(settings.DB_PORT),
        "-U", settings.DB_USER,
        "-d", settings.DB_NAME,
        "-F", "c",  # Custom format
        "-f", str(backup_file)
    ]
    
    try:
        # Выполнение pg_dump
        process = subprocess.run(
            command,
            env={"PGPASSWORD": settings.DB_PASSWORD},
            capture_output=True,
            text=True,
            check=True
        )
        
        file_size = backup_file.stat().st_size / 1024**2  # MB
        logger.info(
            f"Backup created: {backup_file} ({file_size:.2f} MB)"
        )
        
        # Очистка старых backups (старше 30 дней)
        cleanup_old_backups(backup_dir, days=30)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e.stderr}")
        raise


def cleanup_old_backups(backup_dir: Path, days: int = 30) -> None:
    """
    Очистка старых backups.
    
    Args:
        backup_dir: Директория с backups
        days: Хранить backups за последние N дней
    """
    logger.info(f"Cleaning up backups older than {days} days...")
    
    cutoff_time = datetime.utcnow().timestamp() - (days * 86400)
    deleted_count = 0
    
    for backup_file in backup_dir.glob("backup_*.sql"):
        if backup_file.stat().st_mtime < cutoff_time:
            backup_file.unlink()
            deleted_count += 1
            logger.debug(f"Deleted old backup: {backup_file}")
    
    logger.info(f"Cleaned up {deleted_count} old backups")


if __name__ == "__main__":
    asyncio.run(backup_database())
```

---

**ИТОГОВЫЙ ДОКУМЕНТ ЗАВЕРШЕН! Все критичные детали включены!**

**Следующий шаг:** Обновить PYTHON_MIGRATION_README.md с ссылками на части 3 и 4



