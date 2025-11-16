# 🎯 Инструкции для Cursor IDE - Наведение порядка на Production сервере

**Дата создания:** 2025-01-16  
**Проект:** SigmaTrade Bot (Python версия)  
**Сервер:** 34.88.234.78 (europe-north1-a)  
**Текущая готовность:** 98%  
**Цель:** Навести порядок на сервере и подготовить к production деплою

---

## 📋 СОДЕРЖАНИЕ

1. [Текущее состояние проекта](#текущее-состояние-проекта)
2. [Критические задачи (P0)](#критические-задачи-p0)
3. [Важные задачи (P1)](#важные-задачи-p1)
4. [Проверка и валидация](#проверка-и-валидация)
5. [Деплой на сервер](#деплой-на-сервер)
6. [Мониторинг и поддержка](#мониторинг-и-поддержка)

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ ПРОЕКТА

### ✅ Что работает (98%)
- ✅ Все Python модели созданы (User, Deposit, Transaction, etc.)
- ✅ Все repositories реализованы
- ✅ Все services реализованы (включая BlockchainService)
- ✅ Все bot handlers настроены
- ✅ Все middlewares работают
- ✅ FSM states настроены
- ✅ Docker конфигурация готова
- ✅ Миграции Alembic настроены
- ✅ Background jobs (Dramatiq + APScheduler)
- ✅ Документация полная

### ⚠️ Что требует внимания (2%)
- ⚠️ Настройка переменных окружения на сервере
- ⚠️ Финальная проверка всех компонентов
- ⚠️ Тестирование на staging (опционально)
- ⚠️ Настройка backup автоматизации

---

## 🔴 КРИТИЧЕСКИЕ ЗАДАЧИ (P0)

### Задача 1: Проверка и улучшение скриптов развертывания

**Приоритет:** P0 - Критично  
**Файлы:**
- `scripts/server-deploy.sh`
- `scripts/setup-env.sh`
- `scripts/validate-env.py`
- `scripts/check-readiness.sh`

**Действия:**

#### 1.1 Проверить server-deploy.sh
```bash
# Файл: scripts/server-deploy.sh

# ПРОВЕРИТЬ:
# ✅ Все пути корректны
# ✅ Git branch правильный
# ✅ Все команды безопасны
# ✅ Обработка ошибок присутствует
# ✅ Логирование работает

# ДОБАВИТЬ если отсутствует:
# 1. Проверку версии Python (должна быть 3.11+)
# 2. Проверку наличия Docker
# 3. Проверку прав доступа к /opt/sigmatradebot
# 4. Резервное копирование .env перед обновлением
```

#### 1.2 Улучшить validate-env.py
```python
# Файл: scripts/validate-env.py

# ДОБАВИТЬ проверки:
# 1. Проверка формата TELEGRAM_BOT_TOKEN (должен начинаться с цифр и содержать ":")
# 2. Проверка формата WALLET_ADDRESS (должен начинаться с "0x" и быть 42 символа)
# 3. Проверка формата DATABASE_URL (должен быть postgresql+asyncpg://)
# 4. Проверка, что ADMIN_TELEGRAM_IDS содержит только числа
# 5. Проверка RPC_URL (должен быть валидный URL)
# 6. Предупреждение если используются default значения (changeme, etc.)

# ПРИМЕР КОДА:
import re
from urllib.parse import urlparse

def validate_telegram_token(token: str) -> bool:
    """Validate Telegram bot token format."""
    pattern = r'^\d+:[A-Za-z0-9_-]{35}$'
    return bool(re.match(pattern, token))

def validate_wallet_address(address: str) -> bool:
    """Validate Ethereum wallet address."""
    return address.startswith('0x') and len(address) == 42

def validate_database_url(url: str) -> bool:
    """Validate PostgreSQL connection string."""
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme == 'postgresql+asyncpg' and
            parsed.hostname is not None and
            parsed.username is not None
        )
    except:
        return False

# ДОБАВИТЬ в основную функцию валидации
```

#### 1.3 Создать скрипт проверки здоровья
```bash
# Файл: scripts/health-check.sh (СОЗДАТЬ НОВЫЙ)

#!/bin/bash
# Health check script for production server

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}✅${NC} $1"; }
error() { echo -e "${RED}❌${NC} $1"; }
warn() { echo -e "${YELLOW}⚠️${NC} $1"; }

echo "🔍 SigmaTrade Bot - Health Check"
echo "================================"
echo ""

# 1. Check Docker containers
echo "1. Checking Docker containers..."
if docker-compose -f docker-compose.python.yml ps | grep -q "Up"; then
    log "Docker containers are running"
else
    error "Docker containers are not running"
    exit 1
fi

# 2. Check PostgreSQL
echo "2. Checking PostgreSQL..."
if docker exec sigmatrade-postgres pg_isready -U sigmatrade &>/dev/null; then
    log "PostgreSQL is healthy"
else
    error "PostgreSQL is not responding"
    exit 1
fi

# 3. Check Redis
echo "3. Checking Redis..."
if docker exec sigmatrade-redis redis-cli ping &>/dev/null; then
    log "Redis is healthy"
else
    error "Redis is not responding"
    exit 1
fi

# 4. Check Bot logs for errors
echo "4. Checking bot logs for errors..."
ERRORS=$(docker logs sigmatrade-bot --tail 100 2>&1 | grep -i "error\|exception\|traceback" | wc -l)
if [ "$ERRORS" -eq 0 ]; then
    log "No errors in bot logs"
else
    warn "Found $ERRORS errors in bot logs (last 100 lines)"
fi

# 5. Check disk space
echo "5. Checking disk space..."
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    log "Disk space is OK (${DISK_USAGE}% used)"
else
    warn "Disk space is running low (${DISK_USAGE}% used)"
fi

# 6. Check database size
echo "6. Checking database size..."
DB_SIZE=$(docker exec sigmatrade-postgres psql -U sigmatrade -d sigmatrade -t -c "SELECT pg_size_pretty(pg_database_size('sigmatrade'));" | xargs)
log "Database size: $DB_SIZE"

# 7. Check last backup
echo "7. Checking last backup..."
if [ -d "/opt/sigmatradebot/backups" ]; then
    LAST_BACKUP=$(ls -t /opt/sigmatradebot/backups/*.sql.gz 2>/dev/null | head -1)
    if [ -n "$LAST_BACKUP" ]; then
        BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "$LAST_BACKUP")) / 86400 ))
        if [ "$BACKUP_AGE" -le 1 ]; then
            log "Recent backup found (${BACKUP_AGE} days old)"
        else
            warn "Last backup is ${BACKUP_AGE} days old"
        fi
    else
        warn "No backups found"
    fi
else
    warn "Backup directory does not exist"
fi

echo ""
echo "✅ Health check complete!"
```

---

### Задача 2: Проверка и исправление конфигурации Docker

**Приоритет:** P0 - Критично  
**Файлы:**
- `docker-compose.python.yml`
- `Dockerfile.python`
- `docker-entrypoint.sh`

**Действия:**

#### 2.1 Проверить docker-compose.python.yml
```yaml
# Файл: docker-compose.python.yml

# ПРОВЕРИТЬ:
# ✅ Все environment variables правильно передаются
# ✅ Health checks настроены корректно
# ✅ Volumes правильно смонтированы
# ✅ Networks настроены
# ✅ Restart policies установлены

# ДОБАВИТЬ если отсутствует:
services:
  bot:
    # ... существующая конфигурация ...
    
    # ДОБАВИТЬ health check для бота
    healthcheck:
      test: ["CMD-SHELL", "python3 -c 'import asyncio; from bot.main import bot; asyncio.run(bot.get_me())'"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 30s
```

#### 2.2 Улучшить docker-entrypoint.sh
```bash
# Файл: docker-entrypoint.sh

# ДОБАВИТЬ:
# 1. Проверку переменных окружения перед запуском
# 2. Ожидание готовности PostgreSQL и Redis
# 3. Автоматическое применение миграций только для команды "bot"
# 4. Лучшее логирование

# ПРИМЕР УЛУЧШЕНИЙ:

#!/bin/bash
set -e

# Функция ожидания PostgreSQL
wait_for_postgres() {
    echo "⏳ Waiting for PostgreSQL..."
    while ! nc -z postgres 5432; do
        sleep 1
    done
    echo "✅ PostgreSQL is ready"
}

# Функция ожидания Redis
wait_for_redis() {
    echo "⏳ Waiting for Redis..."
    while ! nc -z redis 6379; do
        sleep 1
    done
    echo "✅ Redis is ready"
}

# Проверка критических переменных
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL is not set"
    exit 1
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ ERROR: TELEGRAM_BOT_TOKEN is not set"
    exit 1
fi

# Ожидание сервисов
wait_for_postgres
wait_for_redis

# Применение миграций только для бота
if [ "$1" = "bot" ]; then
    echo "🔄 Running database migrations..."
    alembic upgrade head || {
        echo "❌ Migration failed!"
        echo "📋 Migration status:"
        alembic current
        echo ""
        echo "⚠️  Continuing anyway (set EXIT_ON_MIGRATION_ERROR=true to stop)"
        # exit 1  # Раскомментировать для production
    }
fi

# Запуск команды
case "$1" in
    bot)
        echo "🤖 Starting Telegram Bot..."
        exec python -m bot.main
        ;;
    worker)
        echo "⚙️  Starting Dramatiq Worker..."
        exec dramatiq jobs.broker --processes 2 --threads 4
        ;;
    scheduler)
        echo "⏰ Starting Task Scheduler..."
        exec python -m jobs.scheduler
        ;;
    *)
        exec "$@"
        ;;
esac
```

---

### Задача 3: Проверка настроек безопасности

**Приоритет:** P0 - Критично  
**Файлы:**
- `.env.example`
- `app/config/settings.py`

**Действия:**

#### 3.1 Улучшить .env.example
```bash
# Файл: .env.example

# ДОБАВИТЬ предупреждения и примеры:

# ============= TELEGRAM BOT =============
# Получите токен от @BotFather в Telegram
# Формат: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_BOT_USERNAME=your_bot_username

# ============= DATABASE =============
# PostgreSQL connection string
# Формат: postgresql+asyncpg://username:password@host:port/database
# ⚠️ ВАЖНО: Используйте сильный пароль в production!
DATABASE_URL=postgresql+asyncpg://botuser:STRONG_PASSWORD_HERE@localhost:5432/sigmatradebot
DATABASE_ECHO=false

# ============= ADMIN =============
# Telegram user IDs админов (через запятую)
# Получите свой ID от @userinfobot
ADMIN_TELEGRAM_IDS=123456789,987654321

# ============= WALLET & BLOCKCHAIN =============
# ⚠️ КРИТИЧНО: Храните private key в безопасности!
# Никогда не коммитьте в git!
WALLET_PRIVATE_KEY=your_wallet_private_key_here
WALLET_ADDRESS=0xYourWalletAddress  # Должен начинаться с 0x
USDT_CONTRACT_ADDRESS=0x55d398326f99059fF775485246999027B3197955  # BSC USDT
RPC_URL=https://bsc-dataseed.binance.org/  # BSC mainnet
SYSTEM_WALLET_ADDRESS=0xYourSystemWalletAddress  # Для приема депозитов

# ============= REDIS =============
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Оставьте пустым если нет пароля
REDIS_DB=0

# ============= DEPOSIT LEVELS (в USDT) =============
DEPOSIT_LEVEL_1=50.0
DEPOSIT_LEVEL_2=100.0
DEPOSIT_LEVEL_3=250.0
DEPOSIT_LEVEL_4=500.0
DEPOSIT_LEVEL_5=1000.0

# ============= SECURITY =============
# ⚠️ КРИТИЧНО: Сгенерируйте случайные ключи!
# Используйте: openssl rand -hex 32
SECRET_KEY=your_secret_key_here_generate_with_openssl
ENCRYPTION_KEY=your_encryption_key_here_generate_with_openssl

# ============= APPLICATION =============
ENVIRONMENT=production  # production | development | staging
DEBUG=false  # НИКОГДА не используйте true в production!
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR

# ============= BROADCAST SETTINGS =============
BROADCAST_RATE_LIMIT=15  # сообщений в секунду
BROADCAST_COOLDOWN=900  # 15 минут в секундах

# ============= ROI SETTINGS =============
ROI_DAILY_PERCENT=0.02  # 2% в день
ROI_CAP_MULTIPLIER=5.0  # 500% кап

# ============= POSTGRES (для Docker) =============
# Эти переменные используются docker-compose.python.yml
POSTGRES_DB=sigmatrade
POSTGRES_USER=sigmatrade
POSTGRES_PASSWORD=changeme  # ⚠️ ИЗМЕНИТЕ в production!
POSTGRES_PORT=5432
```

#### 3.2 Добавить валидацию в settings.py
```python
# Файл: app/config/settings.py

# ДОБАВИТЬ дополнительную валидацию:

from pydantic import field_validator, model_validator
import re

class Settings(BaseSettings):
    # ... существующие поля ...

    @field_validator('telegram_bot_token')
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Validate Telegram bot token format."""
        pattern = r'^\d+:[A-Za-z0-9_-]{35}$'
        if not re.match(pattern, v):
            raise ValueError(
                'Invalid Telegram bot token format. '
                'Expected format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz'
            )
        return v

    @field_validator('wallet_address', 'system_wallet_address')
    @classmethod
    def validate_eth_address(cls, v: str) -> str:
        """Validate Ethereum address format."""
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError(
                f'Invalid Ethereum address: {v}. '
                'Must start with 0x and be 42 characters long.'
            )
        return v

    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL."""
        if not v.startswith('postgresql+asyncpg://'):
            raise ValueError(
                'Invalid database URL. Must use postgresql+asyncpg:// driver'
            )
        if 'changeme' in v.lower():
            raise ValueError(
                'Database password cannot be "changeme" in production!'
            )
        return v

    @field_validator('secret_key', 'encryption_key')
    @classmethod
    def validate_keys(cls, v: str) -> str:
        """Validate security keys."""
        if len(v) < 32:
            raise ValueError('Security keys must be at least 32 characters long')
        if v.lower() in ['your_secret_key', 'changeme', 'default']:
            raise ValueError('Please generate a secure random key!')
        return v

    @model_validator(mode='after')
    def validate_production_settings(self) -> 'Settings':
        """Additional validation for production environment."""
        if self.environment == 'production':
            # В production не должно быть DEBUG=true
            if self.debug:
                raise ValueError('DEBUG must be False in production!')
            
            # Проверяем что используются сильные пароли
            if 'changeme' in self.database_url.lower():
                raise ValueError('Change default database password!')
        
        return self

    def get_admin_ids(self) -> list[int]:
        """Parse admin IDs from comma-separated string."""
        if not self.admin_telegram_ids:
            return []
        try:
            return [
                int(id_.strip())
                for id_ in self.admin_telegram_ids.split(",")
                if id_.strip()
            ]
        except ValueError as e:
            raise ValueError(
                f'Invalid admin IDs format: {self.admin_telegram_ids}. '
                f'Must be comma-separated numbers. Error: {e}'
            )
```

---

### Задача 4: Проверка и улучшение обработки ошибок

**Приоритет:** P0 - Критично  
**Файлы:**
- `bot/main.py`
- `bot/middlewares/*.py`
- `app/services/*.py`

**Действия:**

#### 4.1 Улучшить обработку ошибок в bot/main.py
```python
# Файл: bot/main.py

# ДОБАВИТЬ глобальный обработчик ошибок:

from aiogram import Bot, Dispatcher
from aiogram.types import Update, ErrorEvent
from loguru import logger
import traceback

async def error_handler(event: ErrorEvent, bot: Bot) -> None:
    """
    Global error handler for all unhandled exceptions.
    """
    logger.error(
        "Unhandled exception occurred",
        exc_info=event.exception,
        extra={
            "update": event.update.model_dump() if event.update else None,
            "traceback": traceback.format_exc(),
        }
    )
    
    # Уведомить админов о критической ошибке
    admin_ids = settings.get_admin_ids()
    if admin_ids and event.update:
        error_text = (
            "❌ <b>Критическая ошибка!</b>\n\n"
            f"<code>{type(event.exception).__name__}: {str(event.exception)}</code>\n\n"
            f"Update ID: {event.update.update_id if event.update else 'N/A'}"
        )
        
        for admin_id in admin_ids[:3]:  # Уведомляем первых 3 админов
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=error_text,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

# В main():
async def main():
    # ... существующий код ...
    
    # Регистрация глобального обработчика ошибок
    dp.errors.register(error_handler)
    
    # ... остальной код ...
```

---

## 🟡 ВАЖНЫЕ ЗАДАЧИ (P1)

### Задача 5: Создание автоматических тестов

**Приоритет:** P1 - Важно  
**Файлы:**
- `tests/unit/test_settings.py` (СОЗДАТЬ)
- `tests/integration/test_deployment.py` (СОЗДАТЬ)

**Действия:**

#### 5.1 Создать тесты для settings.py
```python
# Файл: tests/unit/test_settings.py (СОЗДАТЬ НОВЫЙ)

import pytest
from pydantic import ValidationError
from app.config.settings import Settings

def test_invalid_telegram_token():
    """Test that invalid Telegram token raises error."""
    with pytest.raises(ValidationError):
        Settings(
            telegram_bot_token="invalid_token",
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            wallet_address="0x" + "a" * 40,
            usdt_contract_address="0x" + "b" * 40,
            rpc_url="https://bsc.example.com",
            system_wallet_address="0x" + "c" * 40,
            secret_key="a" * 32,
            encryption_key="b" * 32,
            admin_telegram_ids="123456789"
        )

def test_invalid_wallet_address():
    """Test that invalid wallet address raises error."""
    with pytest.raises(ValidationError):
        Settings(
            telegram_bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz123",
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            wallet_address="invalid_address",  # Invalid
            usdt_contract_address="0x" + "b" * 40,
            rpc_url="https://bsc.example.com",
            system_wallet_address="0x" + "c" * 40,
            secret_key="a" * 32,
            encryption_key="b" * 32,
            admin_telegram_ids="123456789"
        )

def test_debug_not_allowed_in_production():
    """Test that DEBUG=True is not allowed in production."""
    with pytest.raises(ValidationError):
        Settings(
            telegram_bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz123",
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            wallet_address="0x" + "a" * 40,
            usdt_contract_address="0x" + "b" * 40,
            rpc_url="https://bsc.example.com",
            system_wallet_address="0x" + "c" * 40,
            secret_key="a" * 32,
            encryption_key="b" * 32,
            admin_telegram_ids="123456789",
            environment="production",
            debug=True  # Should fail
        )

def test_weak_password_not_allowed():
    """Test that weak passwords are rejected."""
    with pytest.raises(ValidationError):
        Settings(
            telegram_bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz123",
            database_url="postgresql+asyncpg://user:changeme@localhost/db",  # Weak password
            wallet_address="0x" + "a" * 40,
            usdt_contract_address="0x" + "b" * 40,
            rpc_url="https://bsc.example.com",
            system_wallet_address="0x" + "c" * 40,
            secret_key="a" * 32,
            encryption_key="b" * 32,
            admin_telegram_ids="123456789",
            environment="production"
        )
```

---

### Задача 6: Улучшить документацию деплоя

**Приоритет:** P1 - Важно  
**Файлы:**
- `DEPLOY_TO_SERVER.md`
- `docs/production/DEPLOYMENT.md`

**Действия:**

#### 6.1 Добавить раздел "Типичные проблемы и решения"
```markdown
# Добавить в DEPLOY_TO_SERVER.md:

## 🔧 Типичные проблемы и решения

### Проблема 1: Bot не отвечает на команды

**Симптомы:**
- Бот не отвечает на /start
- В логах нет ошибок

**Решение:**
```bash
# 1. Проверить что бот работает
docker-compose -f docker-compose.python.yml ps

# 2. Проверить логи
docker-compose -f docker-compose.python.yml logs bot | tail -100

# 3. Проверить токен
grep TELEGRAM_BOT_TOKEN .env

# 4. Проверить что бот зарегистрирован
curl -s https://api.telegram.org/bot${BOT_TOKEN}/getMe | jq .

# 5. Перезапустить бота
docker-compose -f docker-compose.python.yml restart bot
```

### Проблема 2: Ошибки подключения к базе данных

**Симптомы:**
- "connection refused" в логах
- "password authentication failed"

**Решение:**
```bash
# 1. Проверить что PostgreSQL работает
docker exec sigmatrade-postgres pg_isready

# 2. Проверить DATABASE_URL
grep DATABASE_URL .env

# 3. Проверить пароль в базе
docker exec -it sigmatrade-postgres psql -U sigmatrade -c "\du"

# 4. Пересоздать базу если нужно
docker-compose -f docker-compose.python.yml down -v
docker-compose -f docker-compose.python.yml up -d postgres
# Подождать 10 секунд
docker-compose -f docker-compose.python.yml up -d
```

### Проблема 3: BlockchainService ошибки

**Симптомы:**
- "Failed to connect to BSC RPC"
- "Invalid RPC URL"

**Решение:**
```bash
# 1. Проверить RPC_URL
grep RPC_URL .env

# 2. Протестировать RPC endpoint
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  https://bsc-dataseed.binance.org/

# 3. Попробовать альтернативные RPC
# - https://bsc-dataseed1.defibit.io/
# - https://bsc-dataseed.bnbchain.org/

# 4. Проверить логи на детали ошибки
docker-compose -f docker-compose.python.yml logs bot | grep -i blockchain
```

### Проблема 4: Миграции не применяются

**Симптомы:**
- "alembic: command not found"
- "No such table"

**Решение:**
```bash
# 1. Вручную применить миграции
docker exec sigmatrade-bot alembic upgrade head

# 2. Проверить текущую версию
docker exec sigmatrade-bot alembic current

# 3. Проверить историю миграций
docker exec sigmatrade-bot alembic history

# 4. Если миграции повреждены, пересоздать базу
docker-compose -f docker-compose.python.yml down
docker volume rm sigmatradebot_postgres_data
docker-compose -f docker-compose.python.yml up -d
```

### Проблема 5: Worker не обрабатывает задачи

**Симптомы:**
- Задачи накапливаются в очереди
- Worker в логах показывает ошибки

**Решение:**
```bash
# 1. Проверить статус worker
docker-compose -f docker-compose.python.yml ps worker

# 2. Проверить логи worker
docker-compose -f docker-compose.python.yml logs worker | tail -100

# 3. Проверить Redis
docker exec sigmatrade-redis redis-cli ping

# 4. Проверить очередь задач
docker exec sigmatrade-redis redis-cli -c "LLEN default"

# 5. Перезапустить worker
docker-compose -f docker-compose.python.yml restart worker
```
```

---

## ✅ ПРОВЕРКА И ВАЛИДАЦИЯ

### Чеклист перед деплоем

**Выполните ВСЕ проверки перед деплоем на production:**

#### 1. Проверка кода
- [ ] Все файлы из P0 задач проверены и исправлены
- [ ] Добавлены все необходимые валидации
- [ ] Обработка ошибок улучшена
- [ ] Тесты созданы и проходят
- [ ] Нет TODO или FIXME в критических местах

#### 2. Проверка скриптов
- [ ] `scripts/server-deploy.sh` - работает корректно
- [ ] `scripts/validate-env.py` - проверяет все переменные
- [ ] `scripts/check-readiness.sh` - все проверки проходят
- [ ] `scripts/health-check.sh` - создан и работает

#### 3. Проверка Docker
- [ ] `docker-compose.python.yml` - конфигурация корректна
- [ ] `Dockerfile.python` - образ собирается без ошибок
- [ ] `docker-entrypoint.sh` - все команды работают
- [ ] Health checks для всех сервисов настроены

#### 4. Проверка безопасности
- [ ] `.env.example` - содержит все переменные и предупреждения
- [ ] `settings.py` - валидация настроек работает
- [ ] Секретные ключи генерируются случайно
- [ ] Нет дефолтных паролей в примерах

#### 5. Проверка документации
- [ ] `DEPLOY_TO_SERVER.md` - актуальна и полная
- [ ] `docs/production/DEPLOYMENT.md` - содержит все инструкции
- [ ] Раздел "Типичные проблемы" добавлен
- [ ] Все команды протестированы

---

## 🚀 ДЕПЛОЙ НА СЕРВЕР

### Подготовка

1. **Локальная проверка:**
```bash
# Запустить все тесты
pytest

# Проверить что все скрипты исполняемые
chmod +x scripts/*.sh

# Валидировать .env.example
cp .env.example .env.test
# Заполнить тестовыми данными
python3 scripts/validate-env.py --env-file .env.test

# Собрать Docker образ локально
docker build -f Dockerfile.python -t sigmatrade:test .

# Проверить что образ работает
docker run --rm sigmatrade:test python -c "import app; import bot; print('OK')"
```

2. **Коммит и пуш изменений:**
```bash
git add .
git commit -m "chore: prepare for production deployment

- Improved validation scripts
- Added health check script
- Enhanced Docker configuration
- Updated documentation
- Added error handling improvements"

git push origin claude/sigmatradebot-python-migration-01UUhWd7yPartmZdGxtPAFLo
```

### Деплой на сервер

**Подключение к серверу:**
```powershell
# Из локальной машины (Windows PowerShell)
gcloud compute ssh sigmatrade-20251108-210354 --zone=europe-north1-a
```

**На сервере выполнить:**
```bash
# 1. Создать директорию проекта
sudo mkdir -p /opt/sigmatradebot
sudo chown -R $USER:$USER /opt/sigmatradebot

# 2. Клонировать репозиторий
cd /opt/sigmatradebot
git clone -b claude/sigmatradebot-python-migration-01UUhWd7yPartmZdGxtPAFLo \
  https://github.com/Avertenandor/sigmatradebot.git .

# 3. Запустить автоматический деплой
chmod +x scripts/*.sh
./scripts/server-deploy.sh

# Скрипт автоматически:
# - Настроит окружение
# - Создаст базу данных
# - Соберет Docker образы
# - Запустит все сервисы
# - Покажет логи

# 4. Проверить здоровье системы
./scripts/health-check.sh
```

---

## 📊 МОНИТОРИНГ И ПОДДЕРЖКА

### Ежедневные проверки

```bash
# Health check
cd /opt/sigmatradebot
./scripts/health-check.sh

# Проверить логи
docker-compose -f docker-compose.python.yml logs --tail=100 --timestamps

# Проверить использование ресурсов
docker stats --no-stream

# Проверить место на диске
df -h
```

### Еженедельные задачи

```bash
# Обновить код
cd /opt/sigmatradebot
git pull origin claude/sigmatradebot-python-migration-01UUhWd7yPartmZdGxtPAFLo

# Пересобрать если были изменения в зависимостях
docker-compose -f docker-compose.python.yml build --no-cache

# Перезапустить сервисы
docker-compose -f docker-compose.python.yml restart

# Проверить backup
ls -lh backups/
```

### Критические алерты

**Настроить уведомления для:**
- Падение любого контейнера
- Использование диска > 80%
- Ошибки в логах бота
- Проблемы с подключением к blockchain
- Неудачные backup

---

## 📝 ИТОГОВЫЙ ЧЕКЛИСТ

**Перед тем как сказать "Готово":**

### Код
- [ ] Все P0 задачи выполнены
- [ ] Валидация settings.py добавлена
- [ ] Обработка ошибок улучшена
- [ ] Health check скрипт создан
- [ ] Тесты написаны и проходят

### Скрипты
- [ ] server-deploy.sh улучшен
- [ ] validate-env.py проверяет все
- [ ] health-check.sh работает
- [ ] Все скрипты исполняемые

### Docker
- [ ] docker-compose.python.yml оптимизирован
- [ ] docker-entrypoint.sh обрабатывает ошибки
- [ ] Health checks добавлены
- [ ] Образ собирается без предупреждений

### Документация
- [ ] DEPLOY_TO_SERVER.md обновлен
- [ ] Типичные проблемы описаны
- [ ] Все команды протестированы
- [ ] Чеклисты актуальны

### Деплой
- [ ] Код закоммичен и запушен
- [ ] Сервер готов к деплою
- [ ] .env заполнен корректными данными
- [ ] База данных создана
- [ ] Все сервисы запущены

### Мониторинг
- [ ] Health check проходит
- [ ] Логи чистые (нет критических ошибок)
- [ ] Backup работает
- [ ] Боту можно отправить /start

---

## 🎯 ЗАКЛЮЧЕНИЕ

Командир, это полный набор инструкций для Cursor IDE.

**Порядок выполнения:**
1. Начать с P0 задач (критично)
2. Проверить все чеклисты
3. Протестировать локально
4. Закоммитить изменения
5. Задеплоить на сервер
6. Проверить работу через health-check

**Ожидаемое время:**
- P0 задачи: 2-3 часа
- P1 задачи: 1-2 часа
- Тестирование: 1 час
- Деплой: 30 минут
- **Итого: 4-6 часов**

**Критичные файлы для проверки:**
1. `scripts/validate-env.py` - добавить валидацию
2. `scripts/health-check.sh` - создать новый
3. `app/config/settings.py` - добавить валидаторы
4. `bot/main.py` - улучшить обработку ошибок
5. `docker-entrypoint.sh` - добавить проверки

---

**Готово к работе! 🚀**

