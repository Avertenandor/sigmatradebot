# 🐍 ТЕХНИЧЕСКОЕ ЗАДАНИЕ: Миграция на Python - ЧАСТЬ 2

**Продолжение документа CLOUD_CODE_PYTHON_MIGRATION.md**

---

## 🤖 МОДУЛЬ 4: Telegram Bot Handlers (bot/handlers/)

### Архитектура handlers

```
Принцип: ТОНКИЕ HANDLERS
- Handler ТОЛЬКО обрабатывает Telegram события
- ВСЯ бизнес-логика в Services
- Максимум 100 строк на handler
```

### Пример: Start Handler

**Файл: `app/bot/handlers/start.py`**
```python
"""Start command handler."""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from loguru import logger

from app.bot.keyboards.main import get_main_keyboard
from app.services.user.user_service import UserService
from app.core.exceptions import UserAlreadyExists

router = Router(name="start")


@router.message(CommandStart())
async def start_handler(
    message: Message,
    user_service: UserService
) -> None:
    """
    Обработка команды /start.
    
    Регистрирует нового пользователя или
    приветствует существующего.
    
    Args:
        message: Telegram сообщение
        user_service: Сервис пользователей
    """
    telegram_id = message.from_user.id
    username = message.from_user.username
    
    # Парсинг реферального кода
    referrer_id = None
    if message.text and len(message.text.split()) > 1:
        ref_code = message.text.split()[1]
        if ref_code.startswith("ref"):
            try:
                referrer_id = int(ref_code[3:])
            except ValueError:
                logger.warning(
                    f"Invalid referral code: {ref_code}"
                )
    
    try:
        # Попытка создать пользователя
        user = await user_service.create_user(
            telegram_id=telegram_id,
            username=username,
            referrer_id=referrer_id
        )
        
        await message.answer(
            f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
            f"Вы успешно зарегистрированы в SigmaTrade Bot.\n"
            f"Используйте меню ниже для навигации.",
            reply_markup=get_main_keyboard()
        )
        
        logger.info(
            f"New user registered: {telegram_id}"
        )
        
    except UserAlreadyExists:
        # Пользователь уже существует
        await message.answer(
            f"С возвращением, {message.from_user.first_name}! 👋\n\n"
            f"Используйте меню ниже:",
            reply_markup=get_main_keyboard()
        )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    """
    Обработка команды /help.
    
    Показывает справку по командам.
    
    Args:
        message: Telegram сообщение
    """
    help_text = (
        "📚 <b>Доступные команды:</b>\n\n"
        "/start - Начало работы\n"
        "/profile - Ваш профиль\n"
        "/deposit - Пополнить баланс\n"
        "/withdraw - Вывести средства\n"
        "/referrals - Реферальная программа\n"
        "/support - Техподдержка\n"
        "/help - Эта справка"
    )
    
    await message.answer(help_text, parse_mode="HTML")
```

### Список ВСЕХ handlers для создания:

#### 1. Common Handlers (handlers/common.py)
```python
- start_handler() - /start
- help_handler() - /help  
- profile_handler() - /profile
- cancel_handler() - отмена операции
```

#### 2. Deposit Handlers (handlers/deposit/)
```python
# deposit_menu.py
- deposit_menu_handler() - показ меню депозита
- deposit_amount_handler() - ввод суммы

# deposit_confirm.py  
- deposit_confirm_handler() - подтверждение
- deposit_cancel_handler() - отмена

# deposit_address.py
- show_deposit_address() - показ адреса
- check_deposit_status() - проверка статуса
```

#### 3. Withdrawal Handlers (handlers/withdrawal/)
```python
# withdrawal_menu.py
- withdrawal_menu_handler() - меню вывода
- withdrawal_amount_input() - ввод суммы

# withdrawal_address.py
- withdrawal_address_input() - ввод адреса
- withdrawal_address_validate() - валидация

# withdrawal_confirm.py
- withdrawal_finpass_input() - ввод finpass
- withdrawal_confirm() - подтверждение
- withdrawal_cancel() - отмена
```

#### 4. Referral Handlers (handlers/referral/)
```python
# referral_info.py
- referral_info_handler() - инфо о программе
- referral_link_handler() - реферальная ссылка

# referral_stats.py
- referral_stats_handler() - статистика
- referral_tree_handler() - дерево рефералов
```

#### 5. Admin Handlers (handlers/admin/)
```python
# admin_menu.py
- admin_menu_handler() - админ меню
- admin_stats_handler() - статистика

# user_management.py
- admin_user_search() - поиск пользователя
- admin_user_info() - инфо о пользователе
- admin_user_edit() - редактирование
- admin_user_ban() - бан
- admin_user_unban() - разбан

# broadcast.py
- admin_broadcast_menu() - меню broadcast
- admin_broadcast_compose() - составление
- admin_broadcast_send() - отправка

# settings.py
- admin_settings_menu() - меню настроек
- admin_settings_edit() - изменение настройки
```

#### 6. Support Handlers (handlers/support/)
```python
# create_ticket.py
- support_menu_handler() - меню support
- ticket_create_category() - выбор категории
- ticket_create_message() - ввод сообщения
- ticket_create_confirm() - создание

# ticket_list.py
- ticket_list_handler() - список тикетов
- ticket_view_handler() - просмотр тикета

# ticket_reply.py
- ticket_reply_input() - ответ на тикет
- ticket_close_handler() - закрытие тикета
```

### Правила для handlers:

```python
# ✅ ПРАВИЛЬНО
@router.message(Command("start"))
async def start_handler(
    message: Message,
    user_service: UserService  # Dependency Injection!
) -> None:
    """Docstring обязателен!"""
    telegram_id = message.from_user.id
    
    # Вызов сервиса
    user = await user_service.get_or_create(telegram_id)
    
    # Отправка ответа
    await message.answer("Hello!")

# ❌ НЕПРАВИЛЬНО
@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    # Без docstring
    # Бизнес-логика В handler (ЗАПРЕЩЕНО!)
    user = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    if not user:
        user = User(telegram_id=message.from_user.id)
        session.add(user)
    await message.answer("Hello!")
```

---

## 📝 МОДУЛЬ 5: Pydantic Schemas (schemas/)

### Зачем нужны схемы?

```
1. Валидация входных данных
2. Сериализация/десериализация
3. API контракты
4. Type hints
```

### Примеры схем

**Файл: `app/schemas/user.py`**
```python
"""User schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator
)


class UserBase(BaseModel):
    """Базовая схема пользователя."""
    
    telegram_id: int = Field(
        ..., 
        gt=0, 
        description="Telegram ID"
    )
    username: Optional[str] = Field(
        None, 
        max_length=255
    )
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Валидация username."""
        if v and v.startswith("@"):
            return v[1:]
        return v


class UserCreate(UserBase):
    """Схема создания пользователя."""
    
    referrer_id: Optional[int] = Field(
        None, 
        gt=0
    )


class UserUpdate(BaseModel):
    """Схема обновления пользователя."""
    
    username: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserResponse(UserBase):
    """Схема ответа с пользователем."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    balance: Decimal
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    # Опциональные связи
    referrer_id: Optional[int] = None


class UserWithStats(UserResponse):
    """Пользователь со статистикой."""
    
    total_deposits: Decimal = Field(
        default=Decimal("0")
    )
    total_withdrawals: Decimal = Field(
        default=Decimal("0")
    )
    referral_count: int = Field(default=0)
    referral_earnings: Decimal = Field(
        default=Decimal("0")
    )
```

**Файл: `app/schemas/deposit.py`**
```python
"""Deposit schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class DepositStatus(str, Enum):
    """Статусы депозита."""
    
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class DepositCreate(BaseModel):
    """Схема создания депозита."""
    
    user_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0, decimal_places=8)
    wallet_address: str = Field(..., min_length=42, max_length=42)


class DepositUpdate(BaseModel):
    """Схема обновления депозита."""
    
    status: Optional[DepositStatus] = None
    transaction_hash: Optional[str] = None
    confirmations: Optional[int] = Field(None, ge=0)


class DepositResponse(BaseModel):
    """Схема ответа с депозитом."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    amount: Decimal
    status: DepositStatus
    wallet_address: str
    transaction_hash: Optional[str] = None
    confirmations: int = 0
    created_at: datetime
    confirmed_at: Optional[datetime] = None
```

### Список ВСЕХ schemas:

1. ✅ user.py - UserCreate, UserUpdate, UserResponse, UserWithStats
2. ✅ deposit.py - DepositCreate, DepositUpdate, DepositResponse
3. ✅ withdrawal.py - WithdrawalCreate, WithdrawalUpdate, WithdrawalResponse
4. ✅ transaction.py - TransactionResponse
5. ✅ referral.py - ReferralResponse, ReferralStats, ReferralTree
6. ✅ reward.py - RewardResponse
7. ✅ notification.py - NotificationCreate, NotificationResponse
8. ✅ support.py - TicketCreate, TicketResponse, MessageCreate
9. ✅ admin.py - AdminStats, BroadcastCreate

---

## 🔄 МОДУЛЬ 6: Background Jobs (jobs/)

### Выбор: Dramatiq

```python
# ✅ Используйте Dramatiq
import dramatiq
from dramatiq.brokers.redis import RedisBroker

redis_broker = RedisBroker(url="redis://localhost:6379/0")
dramatiq.set_broker(redis_broker)

@dramatiq.actor
async def process_deposit(deposit_id: int):
    """Process deposit in background."""
    ...
```

### Broker Setup

**Файл: `app/jobs/broker.py`**
```python
"""Dramatiq broker setup."""
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import (
    AgeLimit,
    TimeLimit,
    Retries,
    Callbacks
)
from loguru import logger

from app.core.config import settings


# Создание брокера
redis_broker = RedisBroker(
    url=settings.REDIS_URL,
    middleware=[
        AgeLimit(),
        TimeLimit(),
        Retries(min_backoff=1000, max_backoff=900000, max_retries=3),
        Callbacks(),
    ]
)

dramatiq.set_broker(redis_broker)

logger.info("Dramatiq broker initialized")
```

### Пример Job: Blockchain Monitor

**Файл: `app/jobs/blockchain_monitor.py`**
```python
"""Blockchain monitoring job."""
import dramatiq
from loguru import logger
from typing import List

from app.database.session import get_session
from app.repositories.deposit import DepositRepository
from app.services.blockchain.blockchain_service import (
    BlockchainService
)
from app.services.deposit.deposit_processor import (
    DepositProcessor
)


@dramatiq.actor(
    queue_name="blockchain",
    time_limit=60000,  # 60 seconds
    max_retries=3
)
async def monitor_pending_deposits() -> None:
    """
    Мониторинг pending депозитов.
    
    Проверяет статус транзакций и обновляет депозиты.
    Запускается каждые 30 секунд.
    """
    logger.info("Starting deposit monitoring")
    
    async with get_session() as session:
        # Получение pending депозитов
        deposit_repo = DepositRepository(session)
        pending = await deposit_repo.get_pending_deposits(
            limit=100
        )
        
        logger.info(
            f"Found {len(pending)} pending deposits"
        )
        
        blockchain_service = BlockchainService()
        deposit_processor = DepositProcessor(
            deposit_repo=deposit_repo,
            blockchain_service=blockchain_service
        )
        
        # Обработка каждого депозита
        for deposit in pending:
            try:
                await deposit_processor.check_deposit_status(
                    deposit.id
                )
            except Exception as e:
                logger.error(
                    f"Error processing deposit {deposit.id}: {e}"
                )
        
        await session.commit()
    
    logger.info("Deposit monitoring completed")


@dramatiq.actor(
    queue_name="blockchain",
    time_limit=120000  # 2 minutes
)
async def scan_blockchain_for_deposits(
    start_block: int,
    end_block: int
) -> None:
    """
    Сканирование блоков на новые депозиты.
    
    Args:
        start_block: Начальный блок
        end_block: Конечный блок
    """
    logger.info(
        f"Scanning blocks {start_block} to {end_block}"
    )
    
    async with get_session() as session:
        blockchain_service = BlockchainService()
        deposit_repo = DepositRepository(session)
        
        # Получение всех активных адресов
        addresses = await deposit_repo.get_active_addresses()
        
        # Сканирование
        transactions = (
            await blockchain_service.scan_blocks_for_addresses(
                addresses=addresses,
                start_block=start_block,
                end_block=end_block
            )
        )
        
        logger.info(
            f"Found {len(transactions)} transactions"
        )
        
        # Обработка найденных транзакций
        for tx in transactions:
            await deposit_repo.update_or_create_from_transaction(
                tx
            )
        
        await session.commit()
```

### Список ВСЕХ jobs:

**1. blockchain_monitor.py**
```python
- monitor_pending_deposits()  # Каждые 30 сек
- scan_blockchain_for_deposits()  # По требованию
- update_deposit_confirmations()  # Каждую минуту
```

**2. payment_processor.py**
```python
- process_pending_withdrawals()  # Каждую минуту
- retry_failed_payments()  # Каждые 5 минут
- process_withdrawal_queue()  # Постоянно
```

**3. reward_calculator.py**
```python
- calculate_daily_roi()  # Каждый день в 00:00
- distribute_referral_rewards()  # При депозите
- calculate_bonus_rewards()  # Раз в неделю
```

**4. notification_sender.py**
```python
- send_pending_notifications()  # Каждые 10 сек
- retry_failed_notifications()  # Каждые 5 минут
```

**5. cleanup.py**
```python
- cleanup_old_sessions()  # Раз в день
- cleanup_old_logs()  # Раз в неделю
- vacuum_database()  # Раз в неделю
```

**6. disk_guard.py**
```python
- monitor_disk_space()  # Каждые 5 минут
- cleanup_if_low_space()  # При необходимости
```

### Scheduler Setup

**Файл: `app/jobs/scheduler.py`**
```python
"""Job scheduler."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.jobs import (
    blockchain_monitor,
    payment_processor,
    reward_calculator,
    notification_sender,
    cleanup,
    disk_guard
)


def setup_scheduler() -> AsyncIOScheduler:
    """
    Настройка планировщика задач.
    
    Returns:
        Настроенный scheduler
    """
    scheduler = AsyncIOScheduler()
    
    # Blockchain monitoring (каждые 30 сек)
    scheduler.add_job(
        blockchain_monitor.monitor_pending_deposits,
        trigger=IntervalTrigger(seconds=30),
        id="monitor_deposits",
        replace_existing=True
    )
    
    # Payment processing (каждую минуту)
    scheduler.add_job(
        payment_processor.process_pending_withdrawals,
        trigger=IntervalTrigger(minutes=1),
        id="process_withdrawals",
        replace_existing=True
    )
    
    # ROI calculation (каждый день в 00:00 UTC)
    scheduler.add_job(
        reward_calculator.calculate_daily_roi,
        trigger=CronTrigger(hour=0, minute=0),
        id="calculate_roi",
        replace_existing=True
    )
    
    # Notification sender (каждые 10 сек)
    scheduler.add_job(
        notification_sender.send_pending_notifications,
        trigger=IntervalTrigger(seconds=10),
        id="send_notifications",
        replace_existing=True
    )
    
    # Cleanup (каждый день в 03:00 UTC)
    scheduler.add_job(
        cleanup.cleanup_old_sessions,
        trigger=CronTrigger(hour=3, minute=0),
        id="cleanup",
        replace_existing=True
    )
    
    # Disk guard (каждые 5 минут)
    scheduler.add_job(
        disk_guard.monitor_disk_space,
        trigger=IntervalTrigger(minutes=5),
        id="disk_guard",
        replace_existing=True
    )
    
    return scheduler
```

---

## ⚙️ МОДУЛЬ 7: Configuration (core/config.py)

**Файл: `app/core/config.py`**
```python
"""Application configuration."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Application
    APP_NAME: str = "SigmaTrade Bot"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(..., min_length=40)
    TELEGRAM_ADMIN_IDS: list[int] = Field(default_factory=list)
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str
    DB_NAME: str = "sigmatrade"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL."""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:"
            f"{self.DB_PASSWORD}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}"
        )
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL."""
        return (
            f"redis://{self.REDIS_HOST}:"
            f"{self.REDIS_PORT}/{self.REDIS_DB}"
        )
    
    # Blockchain
    QUICKNODE_HTTP_URL: str
    QUICKNODE_WSS_URL: str
    BSC_CHAIN_ID: int = 56
    REQUIRED_CONFIRMATIONS: int = 12
    
    # Security
    ENCRYPTION_KEY: str = Field(..., min_length=32)
    SECRET_KEY: str = Field(..., min_length=32)
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 20
    
    # Jobs
    ENABLE_BACKGROUND_JOBS: bool = True
    
    # Referral
    REFERRAL_LEVELS: int = 3
    REFERRAL_REWARDS: list[float] = [0.05, 0.03, 0.02]
    
    # ROI
    MIN_DEPOSIT_AMOUNT: float = 0.01
    MAX_WITHDRAWAL_AMOUNT: float = 100.0


# Singleton instance
settings = Settings()
```

**Файл: `.env.example`**
```bash
# Application
APP_NAME=SigmaTrade Bot
DEBUG=false
LOG_LEVEL=INFO

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_IDS=123456789,987654321

# Database
DB_HOST=postgres
DB_PORT=5432
DB_USER=sigmatrade
DB_PASSWORD=your_secure_password
DB_NAME=sigmatrade

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Blockchain
QUICKNODE_HTTP_URL=https://your-quicknode-url
QUICKNODE_WSS_URL=wss://your-quicknode-url
BSC_CHAIN_ID=56
REQUIRED_CONFIRMATIONS=12

# Security
ENCRYPTION_KEY=your_32_char_encryption_key_here
SECRET_KEY=your_32_char_secret_key_here

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=20

# Jobs
ENABLE_BACKGROUND_JOBS=true

# Referral
REFERRAL_LEVELS=3
REFERRAL_REWARDS=0.05,0.03,0.02

# ROI
MIN_DEPOSIT_AMOUNT=0.01
MAX_WITHDRAWAL_AMOUNT=100.0
```

---

## 🧪 МОДУЛЬ 8: Testing

### Структура тестов

```python
tests/
├── conftest.py              # Общие fixtures
├── unit/                    # Unit tests
│   ├── services/
│   ├── repositories/
│   └── utils/
├── integration/             # Integration tests
│   ├── test_deposit_flow.py
│   └── test_withdrawal_flow.py
└── e2e/                     # End-to-end tests
    └── test_user_journey.py
```

**Файл: `tests/conftest.py`**
```python
"""Pytest fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)

from app.models.base import Base
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    test_engine = create_async_engine(
        settings.DATABASE_URL + "_test",
        echo=True
    )
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()


@pytest.fixture
async def session(
    engine
) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    SessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with SessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def user_service(session):
    """Create user service."""
    from app.repositories.user import UserRepository
    from app.services.user.user_service import UserService
    
    user_repo = UserRepository(session)
    return UserService(user_repo)
```

**Пример теста: `tests/unit/services/test_user_service.py`**
```python
"""User service tests."""
import pytest
from decimal import Decimal

from app.core.exceptions import UserNotFound, InsufficientBalance


@pytest.mark.asyncio
async def test_create_user(user_service):
    """Test user creation."""
    user = await user_service.create_user(
        telegram_id=123456789,
        username="testuser"
    )
    
    assert user.id is not None
    assert user.telegram_id == 123456789
    assert user.username == "testuser"
    assert user.balance == Decimal("0")


@pytest.mark.asyncio
async def test_add_balance(user_service):
    """Test adding balance."""
    user = await user_service.create_user(
        telegram_id=123456789
    )
    
    updated = await user_service.add_balance(
        user.id,
        Decimal("10.5")
    )
    
    assert updated.balance == Decimal("10.5")


@pytest.mark.asyncio
async def test_subtract_balance_insufficient(user_service):
    """Test subtracting more than balance."""
    user = await user_service.create_user(
        telegram_id=123456789
    )
    
    with pytest.raises(InsufficientBalance):
        await user_service.subtract_balance(
            user.id,
            Decimal("100")
        )
```

### Покрытие тестами

```bash
# ✅ ТРЕБУЕТСЯ минимум 80% покрытия
pytest --cov=app --cov-report=html

# Запуск specific тестов
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

---

## 🐳 МОДУЛЬ 9: Docker & Deployment

### Dockerfile

**Файл: `Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY alembic.ini .
COPY scripts/ ./scripts/

# Create non-root user
RUN useradd -m -u 1001 botuser && \
    chown -R botuser:botuser /app

USER botuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s \
  CMD python -c "import sys; sys.exit(0)"

CMD ["python", "-m", "app.main"]
```

### Docker Compose

**Файл: `docker-compose.yml`**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  app:
    build: .
    env_file: .env
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  worker:
    build: .
    env_file: .env
    command: dramatiq app.jobs
    depends_on:
      - postgres
      - redis
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

## ✅ ЧЕК-ЛИСТЫ

### ЧЕКЛИСТ 1: Начало работы

```
[] 1. Создать ветку feature/python-migration
[] 2. Изучить TypeScript код полностью
[] 3. Создать структуру проекта
[] 4. Настроить pyproject.toml / requirements.txt
[] 5. Создать .env.example
[] 6. Настроить .gitignore
```

### ЧЕКЛИСТ 2: Models & Database

```
[] 1. Создать Base model (models/base.py)
[] 2. Мигрировать ВСЕ 19 моделей
[] 3. Проверить relationships
[] 4. Создать alembic миграции
[] 5. Протестировать создание таблиц
```

### ЧЕКЛИСТ 3: Repositories

```
[] 1. Создать BaseRepository
[] 2. Создать ВСЕ 19 репозиториев
[] 3. Покрыть unit тестами (80%+)
```

### ЧЕКЛИСТ 4: Services

```
[] 1. Создать ВСЕ 10 сервисов
[] 2. Покрыть unit тестами (80%+)
[] 3. Протестировать integration тесты
```

### ЧЕКЛИСТ 5: Bot Handlers

```
[] 1. Настроить aiogram 3.x
[] 2. Создать ВСЕ handlers
[] 3. Создать keyboards
[] 4. Создать middlewares
[] 5. Создать filters
[] 6. Настроить FSM states
```

### ЧЕКЛИСТ 6: Background Jobs

```
[] 1. Настроить Dramatiq broker
[] 2. Создать ВСЕ 6 job модулей
[] 3. Настроить scheduler
[] 4. Протестировать jobs локально
```

### ЧЕКЛИСТ 7: Testing

```
[] 1. Настроить pytest
[] 2. Создать fixtures
[] 3. Написать unit tests (80%+ coverage)
[] 4. Написать integration tests
[] 5. Написать e2e tests
[] 6. Запустить все тесты
```

### ЧЕКЛИСТ 8: Docker & Deployment

```
[] 1. Создать Dockerfile
[] 2. Создать docker-compose.yml
[] 3. Протестировать локально
[] 4. Создать README с инструкциями
[] 5. Обновить документацию
```

### ЧЕКЛИСТ 9: Финальная проверка

```
[] 1. Все файлы < 500 строк
[] 2. Все строки < 79 символов
[] 3. Все функции имеют docstrings
[] 4. Все тесты проходят
[] 5. Coverage > 80%
[] 6. Mypy проверка без ошибок
[] 7. Black форматирование применено
[] 8. Ruff линтер без ошибок
[] 9. Docker build успешен
[] 10. Docker compose up успешен
[] 11. Бот отвечает на /start
[] 12. Все функции работают
```

---

## 🚨 КРИТИЧЕСКИЕ ПРАВИЛА

### ЧТО НЕЛЬЗЯ ДЕЛАТЬ НИКОГДА

```
❌ 1. Работать в main ветке
❌ 2. Пропускать функциональность
❌ 3. Создавать файлы > 500 строк
❌ 4. Создавать строки > 79 символов
❌ 5. Пропускать docstrings
❌ 6. Использовать print() вместо logger
❌ 7. Хардкодить значения
❌ 8. Игнорировать ошибки без логирования
❌ 9. Дублировать код
❌ 10. Смешивать бизнес-логику и handlers
```

### ЧТО НУЖНО ДЕЛАТЬ ВСЕГДА

```
✅ 1. Работать в feature/python-migration
✅ 2. Сохранять ВСЮ функциональность
✅ 3. Разбивать большие файлы на модули
✅ 4. Переносить длинные строки
✅ 5. Писать docstrings для всего
✅ 6. Использовать loguru logger
✅ 7. Использовать Settings для конфигурации
✅ 8. Обрабатывать ошибки с логированием
✅ 9. Создавать переиспользуемые функции
✅ 10. Разделять concerns (handlers/services/repos)
```

---

## 📊 ОЦЕНКА ВРЕМЕНИ

```
Модуль 1: Models & Database       - 4-6 часов
Модуль 2: Repositories            - 6-8 часов
Модуль 3: Services                - 10-12 часов
Модуль 4: Bot Handlers            - 8-10 часов
Модуль 5: Schemas                 - 2-3 часа
Модуль 6: Background Jobs         - 4-6 часов
Модуль 7: Configuration           - 1-2 часа
Модуль 8: Testing                 - 6-8 часов
Модуль 9: Docker & Deployment     - 2-3 часа
Финальная проверка                - 2-3 часа

ИТОГО: 35-45 часов
```

---

## 🎯 ФИНАЛЬНАЯ ЦЕЛЬ

```
Полностью рабочий SigmaTrade Bot на Python,
идентичный по функциональности TypeScript версии,
но с лучшим качеством кода, проще в поддержке,
и без TypeScript ошибок.
```

**УСПЕХОВ, CLAUDE CODE! 🚀**

---

*Конец документа*

