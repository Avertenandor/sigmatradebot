# 📋 Памятка команди для деплоя SigmaTrade Bot

**Дата:** 2025-01-16  
**Версия:** Python v1.0  
**Сервер:** 34.88.234.78

---

## 🔐 ПОДКЛЮЧЕНИЕ К СЕРВЕРУ

```powershell
# Из Windows PowerShell
gcloud compute ssh sigmatrade-20251108-210354 --zone=europe-north1-a

# Или через SSH
ssh konfu@34.88.234.78
```

---

## ⚡ БЫСТРЫЙ ДЕПЛОЙ

```bash
# 1. Клонировать репозиторий
sudo mkdir -p /opt/sigmatradebot
sudo chown -R $USER:$USER /opt/sigmatradebot
cd /opt/sigmatradebot
git clone -b claude/sigmatradebot-python-migration-01UUhWd7yPartmZdGxtPAFLo \
  https://github.com/Avertenandor/sigmatradebot.git .

# 2. Запустить автоматический деплой
chmod +x scripts/*.sh
./scripts/server-deploy.sh

# 3. Проверить здоровье
./scripts/health-check.sh
```

---

## 🔧 ОСНОВНЫЕ КОМАНДЫ

### Управление Docker

```bash
# Статус контейнеров
docker-compose -f docker-compose.python.yml ps

# Логи всех сервисов
docker-compose -f docker-compose.python.yml logs -f

# Логи конкретного сервиса
docker-compose -f docker-compose.python.yml logs -f bot
docker-compose -f docker-compose.python.yml logs -f worker
docker-compose -f docker-compose.python.yml logs -f scheduler

# Перезапуск
docker-compose -f docker-compose.python.yml restart

# Остановка
docker-compose -f docker-compose.python.yml down

# Запуск
docker-compose -f docker-compose.python.yml up -d

# Пересборка с обновлением
docker-compose -f docker-compose.python.yml build --no-cache
docker-compose -f docker-compose.python.yml up -d --force-recreate
```

### База данных

```bash
# Подключение к PostgreSQL
docker exec -it sigmatrade-postgres psql -U sigmatrade -d sigmatrade

# Проверка подключения
docker exec sigmatrade-postgres pg_isready -U sigmatrade

# Список таблиц
docker exec sigmatrade-postgres psql -U sigmatrade -d sigmatrade -c "\dt"

# Размер базы данных
docker exec sigmatrade-postgres psql -U sigmatrade -d sigmatrade -c \
  "SELECT pg_size_pretty(pg_database_size('sigmatrade'));"

# Применение миграций вручную
docker exec sigmatrade-bot alembic upgrade head

# Проверка версии миграций
docker exec sigmatrade-bot alembic current

# История миграций
docker exec sigmatrade-bot alembic history
```

### Redis

```bash
# Проверка Redis
docker exec sigmatrade-redis redis-cli ping

# Размер очереди задач
docker exec sigmatrade-redis redis-cli LLEN default

# Очистить все ключи (ОПАСНО!)
# docker exec sigmatrade-redis redis-cli FLUSHALL
```

### Мониторинг

```bash
# Использование ресурсов контейнерами
docker stats --no-stream

# Место на диске
df -h

# Размер Docker volumes
docker system df -v

# Логи системы
sudo journalctl -u docker -n 50

# Просмотр процессов
top
htop  # если установлен
```

---

## 🔍 ДИАГНОСТИКА ПРОБЛЕМ

### Бот не отвечает

```bash
# 1. Проверить статус
docker-compose -f docker-compose.python.yml ps

# 2. Проверить логи на ошибки
docker-compose -f docker-compose.python.yml logs bot | grep -i "error\|exception"

# 3. Проверить токен
grep TELEGRAM_BOT_TOKEN .env

# 4. Проверить подключение к Telegram API
curl -s https://api.telegram.org/bot$(grep TELEGRAM_BOT_TOKEN .env | cut -d'=' -f2)/getMe

# 5. Перезапустить бота
docker-compose -f docker-compose.python.yml restart bot
```

### Ошибки базы данных

```bash
# 1. Проверить PostgreSQL
docker exec sigmatrade-postgres pg_isready

# 2. Проверить DATABASE_URL
grep DATABASE_URL .env

# 3. Проверить логи PostgreSQL
docker-compose -f docker-compose.python.yml logs postgres

# 4. Пересоздать базу (ОПАСНО! Потеря данных!)
docker-compose -f docker-compose.python.yml down -v
docker-compose -f docker-compose.python.yml up -d
```

### Проблемы с BlockchainService

```bash
# 1. Проверить RPC_URL
grep RPC_URL .env

# 2. Проверить подключение к BSC
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  $(grep RPC_URL .env | cut -d'=' -f2)

# 3. Проверить логи на blockchain ошибки
docker-compose -f docker-compose.python.yml logs bot | grep -i "blockchain\|rpc\|bsc"
```

---

## 🔒 БЕЗОПАСНОСТЬ

### Проверка .env файла

```bash
# Проверить права доступа (должно быть 600)
ls -la .env

# Установить правильные права
chmod 600 .env

# Проверить что нет дефолтных паролей
grep -i "changeme\|password\|secret" .env

# Валидация всех переменных
python3 scripts/validate-env.py
```

### Генерация секретных ключей

```bash
# SECRET_KEY
openssl rand -hex 32

# ENCRYPTION_KEY
openssl rand -hex 32

# Пароль для БД
openssl rand -base64 24
```

---

## 💾 BACKUP И RESTORE

### Создание backup

```bash
# Вручную
./scripts/backup-production.sh

# Проверить backups
ls -lh backups/

# Размер последнего backup
ls -lh backups/*.sql.gz | tail -1
```

### Восстановление из backup

```bash
# 1. Найти нужный backup
ls -lt backups/

# 2. Остановить бота
docker-compose -f docker-compose.python.yml stop bot worker scheduler

# 3. Восстановить базу
BACKUP_FILE="backups/sigmatrade_YYYY-MM-DD_HH-MM-SS.sql.gz"
gunzip -c $BACKUP_FILE | docker exec -i sigmatrade-postgres \
  psql -U sigmatrade -d sigmatrade

# 4. Запустить сервисы
docker-compose -f docker-compose.python.yml start bot worker scheduler
```

---

## 📊 ПОЛЕЗНЫЕ ПРОВЕРКИ

### Чеклист после деплоя

```bash
# 1. Health check
./scripts/health-check.sh

# 2. Проверить .env
python3 scripts/validate-env.py

# 3. Проверить контейнеры
docker-compose -f docker-compose.python.yml ps

# 4. Проверить логи (последние 50 строк)
docker-compose -f docker-compose.python.yml logs --tail=50

# 5. Проверить БД
docker exec sigmatrade-postgres psql -U sigmatrade -d sigmatrade -c "SELECT COUNT(*) FROM users;"

# 6. Проверить диск
df -h /

# 7. Отправить /start боту в Telegram
```

### Метрики системы

```bash
# Количество пользователей
docker exec sigmatrade-postgres psql -U sigmatrade -d sigmatrade -c \
  "SELECT COUNT(*) as total_users FROM users;"

# Активные депозиты
docker exec sigmatrade-postgres psql -U sigmatrade -d sigmatrade -c \
  "SELECT COUNT(*) as active_deposits FROM deposits WHERE status = 'active';"

# Общая сумма депозитов
docker exec sigmatrade-postgres psql -U sigmatrade -d sigmatrade -c \
  "SELECT SUM(amount::numeric) as total FROM deposits WHERE status = 'confirmed';"

# Последние ошибки в логах
docker logs sigmatrade-bot --tail 1000 | grep -i "error" | tail -10
```

---

## 🔄 ОБНОВЛЕНИЕ БОТА

```bash
# 1. Создать backup
./scripts/backup-production.sh

# 2. Обновить код
git pull origin claude/sigmatradebot-python-migration-01UUhWd7yPartmZdGxtPAFLo

# 3. Пересобрать образы
docker-compose -f docker-compose.python.yml build

# 4. Применить миграции
docker-compose -f docker-compose.python.yml stop bot worker scheduler
docker exec sigmatrade-bot alembic upgrade head

# 5. Перезапустить сервисы
docker-compose -f docker-compose.python.yml up -d

# 6. Проверить логи
docker-compose -f docker-compose.python.yml logs -f --tail=100

# 7. Health check
./scripts/health-check.sh
```

---

## 📞 ЭКСТРЕННЫЕ ДЕЙСТВИЯ

### Бот упал и не запускается

```bash
# 1. Проверить логи
docker-compose -f docker-compose.python.yml logs bot

# 2. Попробовать перезапустить
docker-compose -f docker-compose.python.yml restart bot

# 3. Если не помогло - пересоздать контейнер
docker-compose -f docker-compose.python.yml up -d --force-recreate bot

# 4. Если все равно не работает - откатиться на backup
# См. раздел "Восстановление из backup"
```

### База данных повреждена

```bash
# 1. Создать аварийный backup (если возможно)
./scripts/backup-production.sh

# 2. Остановить все сервисы
docker-compose -f docker-compose.python.yml down

# 3. Удалить volume (ОПАСНО!)
docker volume rm sigmatradebot_postgres_data

# 4. Запустить PostgreSQL
docker-compose -f docker-compose.python.yml up -d postgres

# 5. Восстановить из последнего backup
# См. раздел "Восстановление из backup"

# 6. Запустить остальные сервисы
docker-compose -f docker-compose.python.yml up -d
```

### Место на диске закончилось

```bash
# 1. Проверить что занимает место
du -sh /* | sort -h

# 2. Очистить Docker
docker system prune -a --volumes -f

# 3. Очистить старые логи
find /var/log -type f -name "*.log" -mtime +30 -delete

# 4. Очистить старые backups (старше 30 дней)
find backups/ -name "*.sql.gz" -mtime +30 -delete

# 5. Проверить место
df -h
```

---

## 📝 ЕЖЕДНЕВНЫЕ ЗАДАЧИ

```bash
# Утренняя проверка (5 минут)
cd /opt/sigmatradebot

# 1. Health check
./scripts/health-check.sh

# 2. Проверить логи на критические ошибки
docker-compose -f docker-compose.python.yml logs --since 24h | \
  grep -i "critical\|fatal" | wc -l

# 3. Проверить место на диске
df -h / | tail -1

# 4. Проверить последний backup
ls -lht backups/ | head -2

# Если все ОК - готово!
```

---

## 🎯 КЛЮЧЕВЫЕ ФАЙЛЫ

```bash
/opt/sigmatradebot/
├── .env                          # Переменные окружения (600)
├── docker-compose.python.yml     # Docker конфигурация
├── scripts/
│   ├── server-deploy.sh         # Автоматический деплой
│   ├── health-check.sh          # Проверка здоровья
│   ├── validate-env.py          # Валидация .env
│   └── backup-production.sh     # Создание backup
├── backups/                      # Backups базы данных
└── logs/                         # Логи приложения
```

---

## 🆘 КОНТАКТЫ

**Документация:**
- [Полное руководство](../production/DEPLOYMENT.md)
- [Устранение проблем](../guides/TROUBLESHOOTING.md)
- [Инструкции для Cursor](CURSOR_INSTRUCTIONS_SERVER_CLEANUP.md)

**Сервер:**
- IP: 34.88.234.78
- Зона: europe-north1-a
- Проект: telegram-bot-444304

---

**Готово! Сохраните эту памятку! 📋**
