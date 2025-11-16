# ⚡ Быстрый старт - Наведение порядка на сервере

**Время выполнения:** 20-30 минут  
**Для:** Cursor IDE  
**Цель:** Быстро подготовить проект к деплою

---

## 🎯 ЧТО НУЖНО СДЕЛАТЬ

### 1. Улучшить валидацию (5 минут)

**Файл:** `scripts/validate-env.py`

```python
# ДОБАВИТЬ в конец файла (перед if __name__ == "__main__":)

def validate_telegram_token(token: str) -> tuple[bool, str]:
    """Validate Telegram bot token format."""
    import re
    pattern = r'^\d+:[A-Za-z0-9_-]{35}$'
    if not re.match(pattern, token):
        return False, "Invalid format. Expected: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    return True, "OK"

def validate_wallet_address(address: str) -> tuple[bool, str]:
    """Validate Ethereum wallet address."""
    if not address or not address.startswith('0x') or len(address) != 42:
        return False, "Must start with 0x and be 42 characters"
    return True, "OK"

def validate_database_url(url: str) -> tuple[bool, str]:
    """Validate database URL."""
    if not url.startswith('postgresql+asyncpg://'):
        return False, "Must use postgresql+asyncpg:// driver"
    if 'changeme' in url.lower():
        return False, "Password cannot be 'changeme'"
    return True, "OK"

# ИСПОЛЬЗОВАТЬ в функции validate_env():
# Добавить вызовы этих функций после проверки наличия переменных
```

---

### 2. Создать health check скрипт (10 минут)

**Файл:** `scripts/health-check.sh` (СОЗДАТЬ НОВЫЙ)

```bash
#!/bin/bash
# SigmaTrade Bot - Health Check

set -euo pipefail

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

# 1. Docker containers
echo "1. Checking Docker containers..."
if docker-compose -f docker-compose.python.yml ps | grep -q "Up"; then
    log "Containers running"
else
    error "Containers not running"
    exit 1
fi

# 2. PostgreSQL
echo "2. Checking PostgreSQL..."
if docker exec sigmatrade-postgres pg_isready -U sigmatrade &>/dev/null; then
    log "PostgreSQL healthy"
else
    error "PostgreSQL not responding"
    exit 1
fi

# 3. Redis
echo "3. Checking Redis..."
if docker exec sigmatrade-redis redis-cli ping &>/dev/null; then
    log "Redis healthy"
else
    error "Redis not responding"
    exit 1
fi

# 4. Bot logs
echo "4. Checking bot logs..."
ERRORS=$(docker logs sigmatrade-bot --tail 100 2>&1 | grep -ic "error\|exception\|traceback" || true)
if [ "$ERRORS" -eq 0 ]; then
    log "No errors in logs"
else
    warn "Found $ERRORS errors in last 100 lines"
fi

# 5. Disk space
echo "5. Checking disk space..."
DISK=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK" -lt 80 ]; then
    log "Disk space OK (${DISK}% used)"
else
    warn "Disk space low (${DISK}% used)"
fi

echo ""
log "Health check complete!"
```

**Сделать исполняемым:**
```bash
chmod +x scripts/health-check.sh
```

---

### 3. Добавить валидацию в settings.py (5 минут)

**Файл:** `app/config/settings.py`

```python
# ДОБАВИТЬ импорты в начало файла:
from pydantic import field_validator, model_validator
import re

# ДОБАВИТЬ в класс Settings (перед model_config):

@field_validator('telegram_bot_token')
@classmethod
def validate_bot_token(cls, v: str) -> str:
    pattern = r'^\d+:[A-Za-z0-9_-]{35}$'
    if not re.match(pattern, v):
        raise ValueError('Invalid Telegram bot token format')
    return v

@field_validator('wallet_address', 'system_wallet_address')
@classmethod
def validate_eth_address(cls, v: str) -> str:
    if not v.startswith('0x') or len(v) != 42:
        raise ValueError(f'Invalid address: {v}')
    return v

@field_validator('database_url')
@classmethod
def validate_database_url(cls, v: str) -> str:
    if not v.startswith('postgresql+asyncpg://'):
        raise ValueError('Must use postgresql+asyncpg:// driver')
    return v

@model_validator(mode='after')
def validate_production(self) -> 'Settings':
    if self.environment == 'production' and self.debug:
        raise ValueError('DEBUG must be False in production')
    return self
```

---

### 4. Улучшить docker-entrypoint.sh (5 минут)

**Файл:** `docker-entrypoint.sh`

```bash
# ДОБАВИТЬ в начало (после set -e):

# Wait for PostgreSQL
wait_for_postgres() {
    echo "⏳ Waiting for PostgreSQL..."
    while ! nc -z postgres 5432; do sleep 1; done
    echo "✅ PostgreSQL ready"
}

# Wait for Redis  
wait_for_redis() {
    echo "⏳ Waiting for Redis..."
    while ! nc -z redis 6379; do sleep 1; done
    echo "✅ Redis ready"
}

# Check critical env vars
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    exit 1
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ ERROR: TELEGRAM_BOT_TOKEN not set"
    exit 1
fi

# ЗАМЕНИТЬ существующий код на:
wait_for_postgres
wait_for_redis

# Run migrations (only for bot)
if [ "$1" = "bot" ]; then
    echo "🔄 Running migrations..."
    alembic upgrade head || echo "⚠️  Migration warning (continuing)"
fi

# Execute command
case "$1" in
    bot)
        echo "🤖 Starting Bot..."
        exec python -m bot.main
        ;;
    worker)
        echo "⚙️  Starting Worker..."
        exec dramatiq jobs.broker --processes 2 --threads 4
        ;;
    scheduler)
        echo "⏰ Starting Scheduler..."
        exec python -m jobs.scheduler
        ;;
    *)
        exec "$@"
        ;;
esac
```

---

### 5. Обновить .env.example (5 минут)

**Файл:** `.env.example`

**ДОБАВИТЬ в начало файла:**

```bash
# =====================================================
# ⚠️  ВНИМАНИЕ! Это шаблон для настройки окружения
# =====================================================
# 1. Скопируйте этот файл: cp .env.example .env
# 2. Заполните ВСЕ обязательные поля
# 3. Сгенерируйте секретные ключи: openssl rand -hex 32
# 4. Никогда не коммитьте .env в git!
# =====================================================
```

**ДОБАВИТЬ комментарии к критичным полям:**

```bash
# ============= WALLET & BLOCKCHAIN =============
# ⚠️ КРИТИЧНО: Храните private key в безопасности!
# Получите от MetaMask или другого кошелька
WALLET_PRIVATE_KEY=your_wallet_private_key_here

# Адрес вашего кошелька (начинается с 0x)
WALLET_ADDRESS=0xYourWalletAddress

# BSC USDT контракт (не меняйте!)
USDT_CONTRACT_ADDRESS=0x55d398326f99059fF775485246999027B3197955

# BSC RPC endpoint
# Публичные: https://bsc-dataseed.binance.org/
# Или используйте платные: QuickNode, Infura, Alchemy
RPC_URL=https://bsc-dataseed.binance.org/

# ============= SECURITY =============
# ⚠️ ОБЯЗАТЕЛЬНО: Сгенерируйте случайные ключи!
# Команда: openssl rand -hex 32
SECRET_KEY=ВАШ_СЛУЧАЙНЫЙ_КЛЮЧ_ЗДЕСЬ_МИНИМУМ_32_СИМВОЛА
ENCRYPTION_KEY=ВАШ_СЛУЧАЙНЫЙ_КЛЮЧ_ЗДЕСЬ_МИНИМУМ_32_СИМВОЛА
```

---

## ✅ ПРОВЕРКА

После выполнения всех изменений:

```bash
# 1. Проверить валидацию
python3 scripts/validate-env.py

# 2. Проверить что скрипт исполняемый
ls -la scripts/health-check.sh

# 3. Собрать Docker образ (для проверки)
docker build -f Dockerfile.python -t sigmatrade:test .

# 4. Запустить тесты
pytest tests/test_imports.py -v

# 5. Проверить settings.py
python3 -c "from app.config.settings import Settings; print('OK')"
```

---

## 🚀 КОММИТ

```bash
git add .
git commit -m "chore: improve deployment scripts and validation

- Enhanced validate-env.py with format checks
- Added health-check.sh script
- Improved settings.py validators
- Better docker-entrypoint.sh error handling
- Updated .env.example with warnings"

git push origin claude/sigmatradebot-python-migration-01UUhWd7yPartmZdGxtPAFLo
```

---

## 📊 РЕЗУЛЬТАТ

После выполнения этих изменений:

✅ Валидация переменных окружения работает  
✅ Health check скрипт готов  
✅ Настройки проверяются автоматически  
✅ Docker запускается с проверками  
✅ Документация обновлена  

**Проект готов к деплою!** 🎉

---

## 📞 СЛЕДУЮЩИЙ ШАГ

Теперь можно:

1. **Задеплоить на сервер:**
   ```bash
   ssh sigmatrade
   cd /opt/sigmatradebot
   ./scripts/server-deploy.sh
   ```

2. **Проверить здоровье:**
   ```bash
   ./scripts/health-check.sh
   ```

3. **Отправить /start боту** в Telegram

---

**Время выполнения: ~30 минут**  
**Готово! 🚀**
