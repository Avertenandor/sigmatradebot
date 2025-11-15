# 🐍 ТЕХНИЧЕСКОЕ ЗАДАНИЕ: Миграция SigmaTrade Bot на Python

**Дата создания:** 2025-11-13  
**Целевой исполнитель:** Claude Code  
**Приоритет:** КРИТИЧЕСКИЙ  
**Оценка времени:** 30-40 часов работы  

---

## 📋 ОГЛАВЛЕНИЕ

1. [Общие требования](#общие-требования)
2. [Правила разработки](#правила-разработки)
3. [Архитектура](#архитектура)
4. [Технологический стек](#технологический-стек)
5. [Структура проекта](#структура-проекта)
6. [Детальная миграция модулей](#детальная-миграция-модулей)
7. [Типизация](#типизация)
8. [База данных](#база-данных)
9. [Конфигурация](#конфигурация)
10. [Тестирование](#тестирование)
11. [Docker и Deployment](#docker-и-deployment)
12. [Чек-листы](#чек-листы)

---

## 🎯 ОБЩИЕ ТРЕБОВАНИЯ

### Цель проекта
Полностью переписать SigmaTrade Telegram Bot с TypeScript на Python, 
сохранив **ВСЮ** функциональность, логику и возможности.

### Критерии успеха
- ✅ 100% функций работают идентично TypeScript версии
- ✅ Все тесты проходят
- ✅ База данных мигрирована корректно
- ✅ Production-ready качество кода
- ✅ Документация обновлена

### Что НЕ ПОТЕРЯТЬ (критично!)

#### 1. Telegram Bot функциональность
- Регистрация пользователей с реферальной системой
- Многоуровневая реферальная программа (2+ уровня)
- Система депозитов через Web3
- Система выводов средств
- Админ-панель (управление пользователями, настройки, статистика)
- Support система (тикеты)
- Broadcast сообщений
- Финансовый пароль (Finpass)
- Блэклист пользователей

#### 2. Blockchain интеграция
- Мониторинг депозитов BNB на BSC
- QuickNode RPC подключение с rate limiting
- Обработка транзакций
- Генерация уникальных адресов для депозитов
- Отслеживание подтверждений блоков
- Dead Letter Queue для failed транзакций

#### 3. База данных
- Полная схема PostgreSQL (19 entities)
- Миграции
- Транзакции и блокировки
- Аудит логирование
- Backup система

#### 4. Background Jobs
- Blockchain мониторинг
- Payment processing
- Reward calculator (ROI система)
- Notification retry
- Cleanup jobs
- Disk guard

#### 5. Security
- Шифрование чувствительных данных
- Secret management (локально + GCP Secret Manager)
- Rate limiting
- Webhook authentication
- SQL injection protection
- XSS protection

---

## 📏 ПРАВИЛА РАЗРАБОТКИ

### ОБЯЗАТЕЛЬНЫЕ ОГРАНИЧЕНИЯ

#### 1. Размер файлов
```
❌ НЕ ДОПУСКАЕТСЯ: файлы > 500 строк
✅ ТРЕБУЕТСЯ: разбивать на модули если превышает
```

**Как разбивать:**
```python
# ПЛОХО - один файл 800 строк
# services/user_service.py

# ХОРОШО - разбито на модули
# services/user/
#   __init__.py        (экспорты)
#   user_service.py    (основная логика, 350 строк)
#   user_validators.py (валидация, 100 строк)
#   user_helpers.py    (вспомогательные, 50 строк)
```

#### 2. Длина строк
```
❌ НЕ ДОПУСКАЕТСЯ: строки > 79 символов
✅ ТРЕБУЕТСЯ: переносить длинные строки
```

**Примеры:**
```python
# ❌ ПЛОХО - 95 символов
user = await session.execute(select(User).where(User.telegram_id == telegram_id).options(joinedload(User.referrals)))

# ✅ ХОРОШО - многострочный запрос
user = await session.execute(
    select(User)
    .where(User.telegram_id == telegram_id)
    .options(joinedload(User.referrals))
)

# ❌ ПЛОХО - длинное сообщение
await message.answer(f"Ваш депозит на сумму {amount} BNB успешно обработан. Баланс: {balance}")

# ✅ ХОРОШО - перенос
await message.answer(
    f"Ваш депозит на сумму {amount} BNB успешно обработан.\n"
    f"Баланс: {balance}"
)
```

#### 3. Работа в ветке
```bash
# ❌ НЕ ДОПУСКАЕТСЯ: работа в main/master
# ✅ ТРЕБУЕТСЯ: создать и работать в отдельной ветке

git checkout -b feature/python-migration
# ВСЯ работа ТОЛЬКО в этой ветке
```

#### 4. Качество кода
```python
# ✅ ТРЕБУЕТСЯ:
- Docstrings для ВСЕХ публичных функций/классов
- Type hints где указано в разделе "Типизация"
- Логирование всех важных операций
- Обработка ошибок везде
- Комментарии для сложной логики

# ❌ НЕ ДОПУСКАЕТСЯ:
- Код без документации
- Хардкод значений
- print() вместо logger
- pass в except без логирования
- Дублирование кода
```

---

## 🏗️ АРХИТЕКТУРА

### Общая схема

```
┌─────────────────┐
│   Telegram Bot  │ (aiogram 3.x)
└────────┬────────┘
         │
    ┌────▼─────┐
    │ Handlers │ (команды, callbacks)
    └────┬─────┘
         │
    ┌────▼──────┐
    │ Services  │ (бизнес-логика)
    └────┬──────┘
         │
    ┌────▼────────────┐
    │  Repositories   │ (работа с БД)
    └────┬────────────┘
         │
    ┌────▼──────┐
    │ Database  │ (SQLAlchemy + asyncpg)
    └───────────┘

Параллельно:
┌──────────────┐
│ Background   │ (Dramatiq workers)
│ Jobs         │
└──────────────┘

┌──────────────┐
│ Blockchain   │ (Web3.py + monitoring)
│ Monitor      │
└──────────────┘
```

### Слои приложения

#### 1. **Presentation Layer** (handlers/)
- Обработка Telegram событий
- Валидация пользовательского ввода
- Формирование ответов
- **НЕ содержит бизнес-логику**

#### 2. **Business Logic Layer** (services/)
- Вся бизнес-логика
- Координация между репозиториями
- Транзакции
- **НЕ знает о Telegram**

#### 3. **Data Access Layer** (repositories/)
- CRUD операции
- Сложные запросы
- **НЕ содержит бизнес-логику**

#### 4. **Domain Layer** (models/)
- Модели данных (SQLAlchemy)
- Pydantic схемы для валидации
- Enums и constants

---

## 🛠️ ТЕХНОЛОГИЧЕСКИЙ СТЕК

### Точные версии (ОБЯЗАТЕЛЬНО использовать эти!)

```toml
# pyproject.toml или requirements.txt

[tool.poetry.dependencies]
python = "^3.11"

# Telegram Bot
aiogram = "^3.3.0"              # НЕ 2.x!
aiohttp = "^3.9.0"

# Database
sqlalchemy = "^2.0.23"          # НЕ 1.4!
alembic = "^1.13.0"
asyncpg = "^0.29.0"
psycopg2-binary = "^2.9.9"      # для alembic

# Web3
web3 = "^6.13.0"                # НЕ 5.x!
eth-account = "^0.10.0"

# Queue/Jobs
dramatiq = { version = "^1.15.0", extras = ["redis"] }
# ИЛИ
celery = { version = "^5.3.4", extras = ["redis"] }

# Redis
redis = "^5.0.1"
hiredis = "^2.3.2"

# Validation
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"

# Encryption
cryptography = "^41.0.7"

# Logging
loguru = "^0.7.2"

# Utils
python-dotenv = "^1.0.0"
pytz = "^2023.3"

# HTTP
httpx = "^0.25.2"

# Development
mypy = "^1.7.1"
black = "^23.12.0"
ruff = "^0.1.8"
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
```

### Почему именно эти библиотеки?

#### aiogram 3.x (НЕ 2.x)
```python
# ✅ ПРАВИЛЬНО - aiogram 3.x
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer("Hello!")

# ❌ НЕПРАВИЛЬНО - aiogram 2.x (старый API)
from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message

@dp.message_handler(commands=['start'])
async def start_handler(message: Message):
    await message.answer("Hello!")
```

#### SQLAlchemy 2.0 (НЕ 1.4)
```python
# ✅ ПРАВИЛЬНО - SQLAlchemy 2.0
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

# ❌ НЕПРАВИЛЬНО - SQLAlchemy 1.4 (устаревший API)
async def get_user(session: AsyncSession, user_id: int):
    return await session.query(User).filter(
        User.id == user_id
    ).first()
```

#### Dramatiq vs Celery
```python
# ✅ РЕКОМЕНДУЕТСЯ - Dramatiq (легче, быстрее)
import dramatiq

@dramatiq.actor
async def process_deposit(deposit_id: int):
    """Обработка депозита."""
    ...

# ✅ АЛЬТЕРНАТИВА - Celery (если нужны сложные workflows)
from celery import Celery

app = Celery('tasks', broker='redis://localhost')

@app.task
def process_deposit(deposit_id: int):
    """Обработка депозита."""
    ...
```

**Выбор:** Используйте **Dramatiq** - он проще и async-native.

---

## 📁 СТРУКТУРА ПРОЕКТА

### Полная структура (создать ВСЮ!)

```
sigmatrade-bot-python/
├── app/
│   ├── __init__.py
│   │
│   ├── main.py                      # Точка входа
│   │
│   ├── bot/                         # Telegram Bot
│   │   ├── __init__.py
│   │   ├── bot.py                   # Инициализация бота
│   │   ├── dispatcher.py            # Настройка роутеров
│   │   │
│   │   ├── handlers/                # Обработчики команд
│   │   │   ├── __init__.py
│   │   │   ├── start.py             # /start команда
│   │   │   ├── profile.py           # Профиль пользователя
│   │   │   ├── deposit/             # Депозиты
│   │   │   │   ├── __init__.py
│   │   │   │   ├── deposit_menu.py
│   │   │   │   ├── deposit_amount.py
│   │   │   │   └── deposit_confirm.py
│   │   │   ├── withdrawal/          # Выводы
│   │   │   │   ├── __init__.py
│   │   │   │   ├── withdrawal_menu.py
│   │   │   │   ├── withdrawal_amount.py
│   │   │   │   └── withdrawal_confirm.py
│   │   │   ├── referral/            # Реферальная система
│   │   │   │   ├── __init__.py
│   │   │   │   ├── referral_info.py
│   │   │   │   └── referral_stats.py
│   │   │   ├── admin/               # Админ панель
│   │   │   │   ├── __init__.py
│   │   │   │   ├── admin_menu.py
│   │   │   │   ├── user_management.py
│   │   │   │   ├── settings.py
│   │   │   │   ├── broadcast.py
│   │   │   │   └── statistics.py
│   │   │   ├── support/             # Support тикеты
│   │   │   │   ├── __init__.py
│   │   │   │   ├── create_ticket.py
│   │   │   │   ├── ticket_list.py
│   │   │   │   └── ticket_reply.py
│   │   │   └── common.py            # Общие handlers
│   │   │
│   │   ├── keyboards/               # Клавиатуры
│   │   │   ├── __init__.py
│   │   │   ├── main.py              # Главное меню
│   │   │   ├── deposit.py
│   │   │   ├── withdrawal.py
│   │   │   ├── referral.py
│   │   │   ├── admin.py
│   │   │   └── support.py
│   │   │
│   │   ├── middlewares/             # Middleware
│   │   │   ├── __init__.py
│   │   │   ├── logging.py           # Логирование событий
│   │   │   ├── auth.py              # Проверка регистрации
│   │   │   ├── admin.py             # Проверка админа
│   │   │   ├── throttling.py        # Rate limiting
│   │   │   └── db_session.py        # Инъекция сессии БД
│   │   │
│   │   ├── filters/                 # Фильтры
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── registered.py
│   │   │   └── chat_type.py
│   │   │
│   │   └── states/                  # FSM States
│   │       ├── __init__.py
│   │       ├── deposit.py
│   │       ├── withdrawal.py
│   │       ├── support.py
│   │       └── admin.py
│   │
│   ├── services/                    # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── user/
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py      # CRUD пользователей
│   │   │   ├── user_validators.py   # Валидация
│   │   │   └── user_helpers.py      # Вспомогательные
│   │   ├── deposit/
│   │   │   ├── __init__.py
│   │   │   ├── deposit_service.py
│   │   │   └── deposit_processor.py
│   │   ├── withdrawal/
│   │   │   ├── __init__.py
│   │   │   ├── withdrawal_service.py
│   │   │   └── withdrawal_processor.py
│   │   ├── referral/
│   │   │   ├── __init__.py
│   │   │   ├── referral_service.py
│   │   │   ├── reward_calculator.py
│   │   │   └── referral_tree.py
│   │   ├── payment/
│   │   │   ├── __init__.py
│   │   │   ├── payment_service.py
│   │   │   └── payment_retry.py
│   │   ├── notification/
│   │   │   ├── __init__.py
│   │   │   ├── notification_service.py
│   │   │   └── notification_retry.py
│   │   ├── support/
│   │   │   ├── __init__.py
│   │   │   └── support_service.py
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── admin_service.py
│   │   │   ├── blacklist_service.py
│   │   │   └── settings_service.py
│   │   ├── blockchain/
│   │   │   ├── __init__.py
│   │   │   ├── blockchain_service.py
│   │   │   ├── transaction_monitor.py
│   │   │   ├── address_generator.py
│   │   │   └── rpc_limiter.py
│   │   └── security/
│   │       ├── __init__.py
│   │       ├── encryption.py
│   │       ├── secret_manager.py
│   │       └── finpass.py
│   │
│   ├── repositories/                # Data Access Layer
│   │   ├── __init__.py
│   │   ├── base.py                  # Базовый репозиторий
│   │   ├── user.py
│   │   ├── deposit.py
│   │   ├── withdrawal.py
│   │   ├── transaction.py
│   │   ├── referral.py
│   │   ├── reward.py
│   │   ├── notification.py
│   │   ├── support_ticket.py
│   │   ├── support_message.py
│   │   ├── blacklist.py
│   │   ├── admin_session.py
│   │   └── settings.py
│   │
│   ├── models/                      # Database Models
│   │   ├── __init__.py
│   │   ├── base.py                  # Base model
│   │   ├── user.py
│   │   ├── deposit.py
│   │   ├── withdrawal.py
│   │   ├── transaction.py
│   │   ├── referral.py
│   │   ├── reward.py
│   │   ├── notification.py
│   │   ├── support.py
│   │   ├── admin.py
│   │   └── settings.py
│   │
│   ├── schemas/                     # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── deposit.py
│   │   ├── withdrawal.py
│   │   ├── transaction.py
│   │   ├── referral.py
│   │   ├── reward.py
│   │   ├── notification.py
│   │   ├── support.py
│   │   └── admin.py
│   │
│   ├── database/                    # Database setup
│   │   ├── __init__.py
│   │   ├── connection.py            # Async engine & session
│   │   ├── session.py               # Session dependency
│   │   └── migrations/              # Alembic migrations
│   │       ├── env.py
│   │       ├── script.py.mako
│   │       └── versions/
│   │           └── (migration files)
│   │
│   ├── jobs/                        # Background jobs
│   │   ├── __init__.py
│   │   ├── broker.py                # Dramatiq broker setup
│   │   ├── blockchain_monitor.py   # Мониторинг депозитов
│   │   ├── payment_processor.py    # Обработка платежей
│   │   ├── reward_calculator.py    # Расчет ROI
│   │   ├── notification_sender.py  # Отправка уведомлений
│   │   ├── cleanup.py              # Очистка старых данных
│   │   └── disk_guard.py           # Мониторинг диска
│   │
│   ├── utils/                       # Утилиты
│   │   ├── __init__.py
│   │   ├── formatting.py            # Форматирование текста
│   │   ├── validation.py            # Валидация данных
│   │   ├── datetime_helpers.py     # Работа с датами
│   │   ├── money.py                 # Денежные операции
│   │   ├── constants.py             # Константы
│   │   └── enums.py                 # Enums
│   │
│   ├── core/                        # Core setup
│   │   ├── __init__.py
│   │   ├── config.py                # Конфигурация
│   │   ├── logging.py               # Настройка логирования
│   │   ├── exceptions.py            # Custom exceptions
│   │   └── dependencies.py          # FastAPI dependencies
│   │
│   └── api/                         # REST API (опционально)
│       ├── __init__.py
│       ├── app.py                   # FastAPI app
│       ├── health.py                # Health check
│       └── webhook.py               # Telegram webhook
│
├── tests/                           # Тесты
│   ├── __init__.py
│   ├── conftest.py                  # Fixtures
│   ├── unit/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── utils/
│   ├── integration/
│   │   ├── test_deposit_flow.py
│   │   ├── test_withdrawal_flow.py
│   │   └── test_referral_system.py
│   └── e2e/
│       └── test_user_journey.py
│
├── scripts/                         # Утилитарные скрипты
│   ├── init_db.py                   # Инициализация БД
│   ├── migrate.py                   # Запуск миграций
│   ├── create_admin.py              # Создание админа
│   └── backup.py                    # Backup БД
│
├── alembic.ini                      # Alembic config
├── pyproject.toml                   # Poetry dependencies
├── requirements.txt                 # Pip dependencies
├── .env.example                     # Пример .env
├── .gitignore
├── README.md
├── Dockerfile
├── docker-compose.yml
└── mypy.ini                         # MyPy config
```

### Правила именования файлов

```python
# ✅ ПРАВИЛЬНО
user_service.py          # snake_case для файлов
deposit_processor.py
referral_tree.py

# ❌ НЕПРАВИЛЬНО
UserService.py           # PascalCase для файлов
depositProcessor.py      # camelCase для файлов
```

---

## 🔄 ДЕТАЛЬНАЯ МИГРАЦИЯ МОДУЛЕЙ

### МОДУЛЬ 1: Database Models (models/)

#### TypeScript → Python mapping

**TypeScript (entities/User.entity.ts):**
```typescript
@Entity('users')
export class User extends BaseEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  telegram_id: number;

  @Column({ nullable: true })
  username?: string;

  @Column({ type: 'decimal', precision: 18, scale: 8, default: 0 })
  balance: number;

  @ManyToOne(() => User, user => user.referrals, { nullable: true })
  referrer?: User;

  @OneToMany(() => User, user => user.referrer)
  referrals: User[];

  @CreateDateColumn()
  created_at: Date;
}
```

**Python (models/user.py):**
```python
"""User model."""
from decimal import Decimal
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, DECIMAL, DateTime, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List

from app.models.base import Base


class User(Base):
    """Модель пользователя."""
    
    __tablename__ = "users"

    # Columns
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    balance: Mapped[Decimal] = mapped_column(
        DECIMAL(18, 8), default=Decimal("0")
    )
    referrer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Relationships
    referrer: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side=[id],
        back_populates="referrals",
        foreign_keys=[referrer_id]
    )
    referrals: Mapped[List["User"]] = relationship(
        "User",
        back_populates="referrer",
        foreign_keys=[referrer_id]
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, "
            f"telegram_id={self.telegram_id})>"
        )
```

#### ВСЕ модели для миграции:

1. ✅ **User** (users)
   - Файл: `app/models/user.py`
   - Поля: id, telegram_id, username, first_name, last_name, 
           balance, referrer_id, is_active, is_verified, 
           registration_date, last_active, created_at, updated_at
   - Relations: referrer, referrals, deposits, withdrawals

2. ✅ **Deposit** (deposits)
   - Файл: `app/models/deposit.py`
   - Поля: id, user_id, amount, status, wallet_address, 
           transaction_hash, confirmations, created_at, 
           confirmed_at
   - Relations: user

3. ✅ **Withdrawal** (withdrawals)
   - Файл: `app/models/withdrawal.py`
   - Поля: id, user_id, amount, status, wallet_address, 
           transaction_hash, fee, created_at, processed_at
   - Relations: user

4. ✅ **Transaction** (transactions)
   - Файл: `app/models/transaction.py`
   - Поля: id, user_id, type, amount, balance_before, 
           balance_after, description, created_at
   - Relations: user

5. ✅ **Referral** (referrals)
   - Файл: `app/models/referral.py`
   - Поля: id, referrer_id, referred_id, level, created_at
   - Relations: referrer, referred

6. ✅ **Reward** (rewards)
   - Файл: `app/models/reward.py`
   - Поля: id, user_id, amount, type, source_user_id, 
           deposit_id, withdrawal_id, created_at
   - Relations: user, source_user, deposit, withdrawal

7. ✅ **Notification** (notifications)
   - Файл: `app/models/notification.py`
   - Поля: id, user_id, type, title, message, is_read, 
           retry_count, created_at, sent_at
   - Relations: user

8. ✅ **SupportTicket** (support_tickets)
   - Файл: `app/models/support.py`
   - Поля: id, user_id, category, status, subject, 
           created_at, updated_at, closed_at
   - Relations: user, messages

9. ✅ **SupportMessage** (support_messages)
   - Файл: `app/models/support.py`
   - Поля: id, ticket_id, sender_type, sender_id, 
           message, created_at
   - Relations: ticket

10. ✅ **Blacklist** (blacklist)
    - Файл: `app/models/admin.py`
    - Поля: id, user_id, reason, banned_by, banned_at, 
            expires_at
    - Relations: user, admin

11. ✅ **AdminSession** (admin_sessions)
    - Файл: `app/models/admin.py`
    - Поля: id, user_id, token, expires_at, created_at
    - Relations: user

12. ✅ **Settings** (settings)
    - Файл: `app/models/settings.py`
    - Поля: id, key, value, type, description, updated_at
    - Relations: none

13. ✅ **UserWallet** (user_wallets)
    - Файл: `app/models/wallet.py`
    - Поля: id, user_id, address, private_key_encrypted, 
            created_at
    - Relations: user

14. ✅ **PaymentRetry** (payment_retries)
    - Файл: `app/models/payment.py`
    - Поля: id, withdrawal_id, attempt_count, last_error, 
            next_retry_at, created_at
    - Relations: withdrawal

15. ✅ **AuditLog** (audit_logs)
    - Файл: `app/models/audit.py`
    - Поля: id, user_id, action, entity_type, entity_id, 
            old_value, new_value, ip_address, created_at
    - Relations: user

16. ✅ **BroadcastMessage** (broadcast_messages)
    - Файл: `app/models/broadcast.py`
    - Поля: id, admin_id, message, image_url, button_text, 
            button_url, sent_count, failed_count, 
            created_at, sent_at
    - Relations: admin

17. ✅ **UserFinancialPassword** (user_financial_passwords)
    - Файл: `app/models/finpass.py`
    - Поля: id, user_id, password_hash, failed_attempts, 
            last_failed_at, created_at
    - Relations: user

18. ✅ **ROIConfiguration** (roi_configurations)
    - Файл: `app/models/roi.py`
    - Поля: id, tier_name, min_amount, max_amount, 
            daily_percent, duration_days, is_active
    - Relations: none

19. ✅ **UserROI** (user_roi)
    - Файл: `app/models/roi.py`
    - Поля: id, user_id, roi_config_id, principal_amount, 
            start_date, end_date, total_earned, last_payout, 
            status
    - Relations: user, roi_config

#### Правила миграции моделей:

```python
# ✅ ОБЯЗАТЕЛЬНО:
1. Все типы полей точно соответствуют TypeORM
2. Все relationships сохранены
3. Все индексы созданы
4. Все constraints (unique, foreign key) на месте
5. Default values идентичны

# ✅ Пример base model (models/base.py):
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base model с общими полями."""
    pass


class TimestampMixin:
    """Mixin для created_at/updated_at."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
```

---

### МОДУЛЬ 2: Repositories (repositories/)

#### Базовый репозиторий

**Файл: `app/repositories/base.py`**
```python
"""Base repository with common CRUD operations."""
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Базовый репозиторий с CRUD операциями.
    
    ОБЯЗАТЕЛЬНО наследуйте от него все репозитории!
    """
    
    def __init__(
        self, 
        model: Type[ModelType], 
        session: AsyncSession
    ) -> None:
        """
        Инициализация репозитория.
        
        Args:
            model: SQLAlchemy модель
            session: Async database session
        """
        self.model = model
        self.session = session
    
    async def get_by_id(
        self, 
        entity_id: int
    ) -> Optional[ModelType]:
        """
        Получить запись по ID.
        
        Args:
            entity_id: ID записи
            
        Returns:
            Найденная запись или None
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelType]:
        """
        Получить все записи с пагинацией.
        
        Args:
            skip: Количество пропускаемых записей
            limit: Максимальное количество записей
            
        Returns:
            Список записей
        """
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> ModelType:
        """
        Создать новую запись.
        
        Args:
            **kwargs: Поля для создания
            
        Returns:
            Созданная запись
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def update(
        self, 
        entity_id: int, 
        **kwargs
    ) -> Optional[ModelType]:
        """
        Обновить запись.
        
        Args:
            entity_id: ID записи
            **kwargs: Поля для обновления
            
        Returns:
            Обновленная запись или None
        """
        await self.session.execute(
            update(self.model)
            .where(self.model.id == entity_id)
            .values(**kwargs)
        )
        await self.session.flush()
        return await self.get_by_id(entity_id)
    
    async def delete(self, entity_id: int) -> bool:
        """
        Удалить запись.
        
        Args:
            entity_id: ID записи
            
        Returns:
            True если удалено, False если не найдено
        """
        result = await self.session.execute(
            delete(self.model).where(self.model.id == entity_id)
        )
        await self.session.flush()
        return result.rowcount > 0
```

#### Пример специфичного репозитория

**Файл: `app/repositories/user.py`**
```python
"""User repository."""
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from app.repositories.base import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository[User]):
    """Репозиторий для работы с пользователями."""
    
    def __init__(self, session) -> None:
        super().__init__(User, session)
    
    async def get_by_telegram_id(
        self, 
        telegram_id: int
    ) -> Optional[User]:
        """
        Получить пользователя по Telegram ID.
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            Пользователь или None
        """
        result = await self.session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_with_referrals(
        self, 
        user_id: int
    ) -> Optional[User]:
        """
        Получить пользователя с рефералами.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Пользователь с загруженными рефералами
        """
        result = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .options(joinedload(User.referrals))
        )
        return result.unique().scalar_one_or_none()
    
    async def update_balance(
        self, 
        user_id: int, 
        amount: Decimal, 
        operation: str = "add"
    ) -> Optional[User]:
        """
        Обновить баланс пользователя.
        
        Args:
            user_id: ID пользователя
            amount: Сумма изменения
            operation: "add" или "subtract"
            
        Returns:
            Обновленный пользователь
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        if operation == "add":
            new_balance = user.balance + amount
        else:
            new_balance = user.balance - amount
        
        if new_balance < 0:
            raise ValueError("Balance cannot be negative")
        
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(balance=new_balance)
        )
        await self.session.flush()
        return await self.get_by_id(user_id)
    
    async def get_active_users(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """
        Получить активных пользователей.
        
        Args:
            skip: Пропустить записей
            limit: Максимум записей
            
        Returns:
            Список активных пользователей
        """
        result = await self.session.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
```

#### Список ВСЕХ репозиториев для создания:

1. ✅ UserRepository (repositories/user.py)
2. ✅ DepositRepository (repositories/deposit.py)
3. ✅ WithdrawalRepository (repositories/withdrawal.py)
4. ✅ TransactionRepository (repositories/transaction.py)
5. ✅ ReferralRepository (repositories/referral.py)
6. ✅ RewardRepository (repositories/reward.py)
7. ✅ NotificationRepository (repositories/notification.py)
8. ✅ SupportTicketRepository (repositories/support_ticket.py)
9. ✅ SupportMessageRepository (repositories/support_message.py)
10. ✅ BlacklistRepository (repositories/blacklist.py)
11. ✅ AdminSessionRepository (repositories/admin_session.py)
12. ✅ SettingsRepository (repositories/settings.py)
13. ✅ UserWalletRepository (repositories/user_wallet.py)
14. ✅ PaymentRetryRepository (repositories/payment_retry.py)
15. ✅ AuditLogRepository (repositories/audit_log.py)
16. ✅ BroadcastRepository (repositories/broadcast.py)
17. ✅ FinpassRepository (repositories/finpass.py)
18. ✅ ROIConfigRepository (repositories/roi_config.py)
19. ✅ UserROIRepository (repositories/user_roi.py)

---

### МОДУЛЬ 3: Services (services/)

#### Структура сервиса

**ОБЯЗАТЕЛЬНО следовать этому паттерну:**

```python
"""
Структура КАЖДОГО сервиса:

1. Импорты
2. Logger
3. Класс сервиса
4. __init__ (инъекция зависимостей)
5. Публичные методы (async)
6. Приватные методы (async, prefix _)
7. Валидация (отдельный файл если > 100 строк)
"""
```

**Файл: `app/services/user/user_service.py`**
```python
"""User service."""
from typing import Optional, List
from decimal import Decimal
from loguru import logger

from app.repositories.user import UserRepository
from app.repositories.transaction import TransactionRepository
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User
from app.core.exceptions import (
    UserNotFound,
    InsufficientBalance
)


class UserService:
    """Сервис для работы с пользователями."""
    
    def __init__(
        self,
        user_repo: UserRepository,
        transaction_repo: TransactionRepository
    ) -> None:
        """
        Инициализация сервиса.
        
        Args:
            user_repo: Репозиторий пользователей
            transaction_repo: Репозиторий транзакций
        """
        self.user_repo = user_repo
        self.transaction_repo = transaction_repo
    
    async def create_user(
        self, 
        telegram_id: int,
        username: Optional[str] = None,
        referrer_id: Optional[int] = None
    ) -> User:
        """
        Создать нового пользователя.
        
        Args:
            telegram_id: Telegram ID
            username: Username (опционально)
            referrer_id: ID реферера (опционально)
            
        Returns:
            Созданный пользователь
            
        Raises:
            ValueError: Если пользователь уже существует
        """
        logger.info(
            f"Creating user: telegram_id={telegram_id}, "
            f"referrer_id={referrer_id}"
        )
        
        # Проверка существования
        existing = await self.user_repo.get_by_telegram_id(
            telegram_id
        )
        if existing:
            raise ValueError(
                f"User {telegram_id} already exists"
            )
        
        # Создание
        user = await self.user_repo.create(
            telegram_id=telegram_id,
            username=username,
            referrer_id=referrer_id,
            balance=Decimal("0"),
            is_active=True,
            is_verified=False
        )
        
        logger.info(f"User created: id={user.id}")
        return user
    
    async def get_user(
        self, 
        user_id: int
    ) -> User:
        """
        Получить пользователя по ID.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Пользователь
            
        Raises:
            UserNotFound: Если пользователь не найден
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFound(f"User {user_id} not found")
        return user
    
    async def add_balance(
        self,
        user_id: int,
        amount: Decimal,
        description: str = "Balance added"
    ) -> User:
        """
        Добавить средства на баланс.
        
        Args:
            user_id: ID пользователя
            amount: Сумма для добавления
            description: Описание транзакции
            
        Returns:
            Обновленный пользователь
            
        Raises:
            UserNotFound: Если пользователь не найден
            ValueError: Если сумма <= 0
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        logger.info(
            f"Adding balance: user_id={user_id}, "
            f"amount={amount}"
        )
        
        user = await self.get_user(user_id)
        balance_before = user.balance
        
        # Обновление баланса
        user = await self.user_repo.update_balance(
            user_id, amount, operation="add"
        )
        
        # Создание транзакции
        await self.transaction_repo.create(
            user_id=user_id,
            type="credit",
            amount=amount,
            balance_before=balance_before,
            balance_after=user.balance,
            description=description
        )
        
        logger.info(
            f"Balance added: user_id={user_id}, "
            f"new_balance={user.balance}"
        )
        return user
    
    async def subtract_balance(
        self,
        user_id: int,
        amount: Decimal,
        description: str = "Balance subtracted"
    ) -> User:
        """
        Списать средства с баланса.
        
        Args:
            user_id: ID пользователя
            amount: Сумма для списания
            description: Описание транзакции
            
        Returns:
            Обновленный пользователь
            
        Raises:
            UserNotFound: Если пользователь не найден
            InsufficientBalance: Если недостаточно средств
            ValueError: Если сумма <= 0
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        logger.info(
            f"Subtracting balance: user_id={user_id}, "
            f"amount={amount}"
        )
        
        user = await self.get_user(user_id)
        
        if user.balance < amount:
            raise InsufficientBalance(
                f"Insufficient balance: has {user.balance}, "
                f"needs {amount}"
            )
        
        balance_before = user.balance
        
        # Обновление баланса
        user = await self.user_repo.update_balance(
            user_id, amount, operation="subtract"
        )
        
        # Создание транзакции
        await self.transaction_repo.create(
            user_id=user_id,
            type="debit",
            amount=amount,
            balance_before=balance_before,
            balance_after=user.balance,
            description=description
        )
        
        logger.info(
            f"Balance subtracted: user_id={user_id}, "
            f"new_balance={user.balance}"
        )
        return user
```

#### Список ВСЕХ сервисов для создания:

**1. User Service (services/user/)**
- `user_service.py` - CRUD, баланс, регистрация
- `user_validators.py` - валидация данных
- Методы: create_user, get_user, update_user, add_balance, 
          subtract_balance, verify_user, deactivate_user

**2. Deposit Service (services/deposit/)**
- `deposit_service.py` - создание депозитов
- `deposit_processor.py` - обработка депозитов
- Методы: create_deposit, process_deposit, confirm_deposit,
          get_user_deposits, get_pending_deposits

**3. Withdrawal Service (services/withdrawal/)**
- `withdrawal_service.py` - создание выводов
- `withdrawal_processor.py` - обработка выводов
- Методы: create_withdrawal, process_withdrawal, 
          cancel_withdrawal, get_user_withdrawals

**4. Referral Service (services/referral/)**
- `referral_service.py` - управление рефералами
- `reward_calculator.py` - расчет наград
- `referral_tree.py` - построение дерева рефералов
- Методы: get_referrals, calculate_rewards, 
          get_referral_tree, get_referral_stats

**5. Payment Service (services/payment/)**
- `payment_service.py` - обработка платежей
- `payment_retry.py` - retry логика
- Методы: process_payment, retry_payment, 
          cancel_payment

**6. Notification Service (services/notification/)**
- `notification_service.py` - отправка уведомлений
- `notification_retry.py` - retry логика
- Методы: send_notification, retry_notification,
          get_user_notifications, mark_as_read

**7. Support Service (services/support/)**
- `support_service.py` - тикеты и сообщения
- Методы: create_ticket, add_message, close_ticket,
          get_user_tickets, get_open_tickets

**8. Admin Service (services/admin/)**
- `admin_service.py` - админ функции
- `blacklist_service.py` - блэклист
- `settings_service.py` - настройки
- Методы: get_statistics, manage_user, broadcast,
          update_settings, ban_user, unban_user

**9. Blockchain Service (services/blockchain/)**
- `blockchain_service.py` - Web3 операции
- `transaction_monitor.py` - мониторинг транзакций
- `address_generator.py` - генерация адресов
- `rpc_limiter.py` - rate limiting для RPC
- Методы: get_balance, send_transaction, 
          monitor_deposits, generate_address

**10. Security Service (services/security/)**
- `encryption.py` - шифрование данных
- `secret_manager.py` - управление секретами
- `finpass.py` - финансовый пароль
- Методы: encrypt, decrypt, verify_finpass, 
          set_finpass, get_secret

---

**МАКСИМАЛЬНАЯ ДЛИНА: Этот документ слишком большой. Разбиваю на 2 части.**

Продолжить создание документа? Осталось описать:
- Handlers (bot/)
- Schemas (Pydantic)
- Background Jobs
- Configuration
- Testing
- Docker
- Чек-листы

Создать ЧАСТЬ 2 документа?

