# 📋 Текущая конфигурация сервера (для справки)

**Дата:** 2025-11-14  
**Версия:** TypeScript (перед миграцией на Python)

---

## 🖥️ Информация о сервере

| Параметр | Значение |
|----------|----------|
| **Имя инстанса** | sigmatrade-20251108-210354 |
| **Внешний IP** | 34.88.234.78 |
| **Внутренний IP** | 10.166.0.3 |
| **Зона** | europe-north1-a (Finland) |
| **Проект GCP** | telegram-bot-444304 |
| **Тип машины** | e2-medium (2 vCPU, 4 GB RAM) |
| **ОС** | Debian 12 (bookworm) |
| **Диск** | 10 GB (6.5 GB свободно) |

---

## 🐳 Docker конфигурация

### Сервисы

1. **sigmatrade_postgres**
   - Образ: `postgres:15-alpine`
   - Порт: `5432:5432`
   - Volume: `postgres_data:/var/lib/postgresql/data`
   - База: `sigmatrade`
   - Пользователь: `botuser`

2. **sigmatrade_redis**
   - Образ: `redis:7-alpine`
   - Порт: `6379:6379`
   - Volume: `redis_data:/data`
   - Режим: `appendonly yes`

3. **sigmatrade_app**
   - Образ: Custom build (Node.js TypeScript)
   - Порт: `3000:3000`
   - Volumes:
     - `./backups:/app/backups`
     - `./logs:/app/logs`
   - Зависимости: postgres, redis

4. **sigmatrade_nginx** (опционально)
   - Образ: `nginx:alpine`
   - Порты: `80:80`, `443:443`
   - Profile: production

### Docker Volumes

```
sigmatrade_postgres_data    local
sigmatrade_redis_data       local
```

### Docker Network

```
sigmatrade_network          bridge
```

---

## 🗄️ База данных (PostgreSQL)

### Основные таблицы

| Таблица | Описание | Примерный размер |
|---------|----------|------------------|
| `users` | Пользователи бота | ~1000-10000 записей |
| `deposits` | Депозиты пользователей | ~5000-50000 записей |
| `withdrawals` | Выводы средств | ~1000-10000 записей |
| `transactions` | Все транзакции | ~10000-100000 записей |
| `referrals` | Реферальные связи | ~500-5000 записей |
| `support_tickets` | Тикеты поддержки | ~100-1000 записей |
| `admins` | Администраторы | ~5-20 записей |
| `payment_retries` | Повторы платежей | ~100-1000 записей |
| `failed_notifications` | Неудачные уведомления | ~50-500 записей |
| `migrations` | История миграций | ~20-50 записей |

### Индексы (критичные)

```sql
-- Deposits
IDX_deposits_processing
IDX_deposits_user_id

-- Transactions
IDX_transactions_tx_hash_unique
IDX_transactions_user_id

-- Users
IDX_users_telegram_id
IDX_users_wallet_address

-- Payment Retries
IDX_payment_retries_status
IDX_payment_retries_next_retry

-- Failed Notifications
IDX_failed_notifications_status
IDX_failed_notifications_next_retry
```

### Размер БД

```bash
# Проверить размер
SELECT pg_size_pretty(pg_database_size('sigmatrade'));

# Ожидаемый размер: 50-500 MB (зависит от истории)
```

---

## 🔴 Redis конфигурация

### Ключи и очереди (Bull)

| Ключ/Очередь | Назначение |
|--------------|------------|
| `bull:blockchain-monitor:*` | Мониторинг блокчейна |
| `bull:payment-processor:*` | Обработка платежей |
| `bull:payment-retry:*` | Повтор неудачных платежей |
| `bull:notification-retry:*` | Повтор уведомлений |
| `bull:reward-calculator:*` | Расчет наград |
| `bull:backup-scheduler:*` | Автобэкапы |
| `bull:cleanup-scheduler:*` | Очистка старых данных |
| `bull:disk-guard:*` | Контроль диска |
| `bull:broadcast-processor:*` | Рассылки |

### Сессии и rate limiting

| Ключ | Назначение |
|------|------------|
| `session:*` | Сессии пользователей |
| `ratelimit:*` | Ограничения частоты запросов |
| `ban:*` | Заблокированные пользователи |

---

## ⚙️ Переменные окружения (.env)

### Telegram

```bash
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_WEBHOOK_DOMAIN=  # если используется webhook
```

### База данных

```bash
DB_HOST=postgres  # или localhost для локальной БД
DB_PORT=5432
DB_USERNAME=botuser
DB_PASSWORD=your_password_here
DB_DATABASE=sigmatrade
DB_LOGGING=false
```

### Redis

```bash
REDIS_HOST=redis  # или localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # если установлен
```

### Blockchain (BSC)

```bash
QUICKNODE_HTTPS_URL=https://XXX.bsc.quiknode.pro/XXX/
QUICKNODE_WSS_URL=wss://XXX.bsc.quiknode.pro/XXX/
BSC_CHAIN_ID=56
BSC_START_BLOCK=your_start_block_number
BSC_CONFIRMATION_BLOCKS=12
```

### Контракты и кошельки

```bash
USDT_CONTRACT=0x55d398326f99059fF775485246999027B3197955
SYSTEM_WALLET_ADDRESS=0xYOUR_SYSTEM_WALLET
PAYOUT_WALLET_ADDRESS=0xYOUR_PAYOUT_WALLET
```

### Уровни депозитов (BNB)

```bash
DEPOSIT_LEVEL_1=0.05
DEPOSIT_LEVEL_2=0.1
DEPOSIT_LEVEL_3=0.25
DEPOSIT_LEVEL_4=0.5
DEPOSIT_LEVEL_5=1.0
DEPOSIT_LEVEL_6=2.5
```

### Реферальная система

```bash
REFERRAL_RATE_LEVEL_1=0.05
REFERRAL_RATE_LEVEL_2=0.04
REFERRAL_RATE_LEVEL_3=0.03
REFERRAL_ENABLED=true
MAX_REFERRAL_DEPTH=3
```

### Безопасность

```bash
ADMIN_MASTER_KEY=your_master_key_here
ENCRYPTION_KEY=your_encryption_key_here
SESSION_KEY=your_session_key_here
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=20
```

### Обработка депозитов

```bash
DEPOSIT_BATCH_SIZE=10
DEPOSIT_CONCURRENCY=3
```

### Логирование

```bash
LOG_LEVEL=info
LOG_MAX_FILES=30
LOG_MAX_SIZE=20971520  # 20 MB
```

### Мониторинг

```bash
PERFORMANCE_REPORT_INTERVAL_MS=300000  # 5 минут
MEMORY_THRESHOLD_PERCENT=80
CPU_THRESHOLD_PERCENT=90
EVENT_LOOP_LAG_THRESHOLD_MS=100
```

---

## 📦 Зависимости (package.json)

### Основные

```json
{
  "telegraf": "^4.16.3",
  "typeorm": "^0.3.20",
  "pg": "^8.11.3",
  "ethers": "^6.11.1",
  "ioredis": "^5.3.2",
  "bull": "^4.12.2",
  "winston": "^3.11.0",
  "dotenv": "^16.4.1"
}
```

### Версии

- Node.js: 20+
- TypeScript: 5.3+
- PostgreSQL: 15
- Redis: 7

---

## 🔄 Background Jobs (Bull Queues)

| Job | Интервал | Назначение |
|-----|----------|------------|
| `blockchain-monitor` | Real-time | WebSocket мониторинг блоков |
| `payment-processor` | Real-time | Обработка входящих депозитов |
| `payment-retry` | Каждые 5 минут | Повтор неудачных платежей |
| `notification-retry` | Каждые 5 минут | Повтор уведомлений |
| `reward-calculator` | Каждый час | Расчет и выплата наград |
| `backup-scheduler` | Раз в день (3:00 AM) | Автоматические бэкапы |
| `cleanup-scheduler` | Раз в день (4:00 AM) | Очистка старых записей |
| `disk-guard` | Каждый час | Проверка места на диске |
| `broadcast-processor` | Real-time | Массовые рассылки |

---

## 📊 Производительность

### Метрики (текущие)

| Метрика | Значение |
|---------|----------|
| **Memory Usage** | ~800 MB - 1.2 GB |
| **CPU Usage** | 5-15% (idle), до 50% (peak) |
| **Event Loop Lag** | < 50ms (normal) |
| **RPC Requests/min** | 10-100 (зависит от активности) |
| **Database Connections** | 5-10 активных |
| **Redis Keys** | 100-1000 |

### Лимиты

```bash
# Database connection pool
max: 20
min: 2

# Redis connection pool
max: 10

# Rate limiting
20 requests per minute per user
```

---

## 🛡️ Безопасность

### Firewall Rules (GCP)

| Правило | Порт | Источник | Назначение |
|---------|------|----------|------------|
| `default-allow-ssh` | 22 | 0.0.0.0/0 | SSH доступ |
| `allow-http` | 80 | 0.0.0.0/0 | HTTP (nginx) |
| `allow-https` | 443 | 0.0.0.0/0 | HTTPS (nginx) |

### Service Account

```
Email: claude-admin-528@telegram-bot-444304.iam.gserviceaccount.com
Key: telegram-bot-444304-2808e7f2ef6c.json
Roles: Compute Admin, Storage Admin
```

---

## 🔧 Скрипты (package.json)

```json
{
  "dev": "ts-node-dev src/index.ts",
  "build": "tsc",
  "start": "node dist/index.js",
  "test": "jest",
  "migration:generate": "typeorm migration:generate",
  "migration:run": "typeorm migration:run",
  "migration:revert": "typeorm migration:revert",
  "docker": "docker-compose up -d",
  "docker:logs": "docker-compose logs -f",
  "docker:down": "docker-compose down",
  "backup": "node scripts/backup.js",
  "restore": "node scripts/restore.js"
}
```

---

## 📁 Структура директорий

```
/opt/sigmatrade/
├── src/
│   ├── bot/
│   │   ├── handlers/
│   │   │   ├── user/
│   │   │   └── admin/
│   │   ├── keyboards/
│   │   ├── middlewares/
│   │   └── index.ts
│   ├── services/
│   │   ├── admin.service.ts
│   │   ├── blockchain/
│   │   ├── notification.service.ts
│   │   ├── deposit.service.ts
│   │   ├── withdrawal.service.ts
│   │   └── ...
│   ├── database/
│   │   ├── entities/
│   │   ├── migrations/
│   │   └── data-source.ts
│   ├── jobs/
│   ├── utils/
│   ├── config/
│   └── index.ts
├── docs/
├── logs/
├── backups/
├── data/
├── node_modules/
├── package.json
├── tsconfig.json
├── docker-compose.yml
├── Dockerfile
└── .env
```

---

## 🚨 Известные проблемы

### 1. Race Conditions в депозитах
**Решено:** Добавлены транзакции и индексы

### 2. Потеря уведомлений
**Решено:** Добавлена система retry (payment-retry, notification-retry)

### 3. Webhook latency
**Решено:** Переход на WebSocket QuickNode

### 4. Memory leaks
**Решено:** Graceful shutdown, performance monitoring

---

## 📞 Контакты для миграции

### Файлы для переноса в Python

1. **Критичная логика:**
   - `src/services/blockchain/deposit-processor.ts`
   - `src/services/blockchain/event-monitor.ts`
   - `src/database/entities/*.entity.ts`

2. **Middleware:**
   - `src/bot/middlewares/request-id.middleware.ts`
   - `src/bot/middlewares/auth.middleware.ts`
   - `src/bot/middlewares/rateLimit.middleware.ts`

3. **Background Jobs:**
   - `src/jobs/*.job.ts`

4. **Утилиты:**
   - `src/utils/logger.util.ts`
   - `src/utils/encryption.util.ts`
   - `src/utils/performance-monitor.util.ts`

---

## 📝 Замечания для Python миграции

### Требуется реализовать:

1. **Аналоги TypeORM:**
   - SQLAlchemy 2.0 + Alembic
   - Pydantic для валидации

2. **Аналоги Bull:**
   - Celery + Redis
   - или ARQ (async)

3. **Аналоги Telegraf:**
   - aiogram 3.x (рекомендуется)
   - python-telegram-bot (альтернатива)

4. **Аналоги Ethers.js:**
   - web3.py
   - eth-account (для подписей)

5. **Graceful Shutdown:**
   - asyncio signal handlers
   - contextlib.AsyncExitStack

6. **Performance Monitoring:**
   - psutil (CPU, memory)
   - prometheus_client (метрики)

---

**Эта конфигурация актуальна на момент миграции.**  
**Используйте её как справочник при переносе на Python.**

---

**Сохранено:** 2025-11-14  
**Для миграции:** TypeScript → Python 3.11  
**Автор:** Claude AI Assistant

