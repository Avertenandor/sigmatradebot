# 🔄 Гайд по миграции сервера на Python версию

## 📋 Краткая информация

| Параметр | Значение |
|----------|----------|
| **Сервер** | sigmatrade-20251108-210354 |
| **IP** | 34.88.234.78 |
| **Зона** | europe-north1-a |
| **Проект** | telegram-bot-444304 |
| **Директория** | /opt/sigmatrade |
| **Текущая версия** | TypeScript + Node.js |
| **Целевая версия** | Python 3.11 |

---

## 🚀 Быстрый старт (для Windows/PowerShell)

### Шаг 1: Запустить автоматическую очистку

```powershell
# Из директории C:\Users\konfu\Desktop\sigmatradebot\
.\cleanup_server.ps1
```

Этот скрипт автоматически:
- ✅ Проверит статус сервера
- ✅ Создаст полный бэкап (БД + код + конфигурация)
- ✅ Остановит Docker контейнеры
- ✅ Очистит TypeScript файлы
- ✅ Установит Python 3.11 + Poetry
- ✅ Создаст структуру для Python проекта

**Время выполнения:** 5-10 минут

---

## 📝 Что будет сделано

### ✅ Сохранено (бэкапы)
- PostgreSQL база данных (полный дамп)
- Redis данные
- Все логи
- Конфигурация (.env файл)
- TypeScript код (архив)
- docker-compose.yml

**Локация бэкапов:** `/opt/sigmatrade/backups/typescript_final_YYYYMMDD_HHMMSS/`

### 🗑️ Будет удалено
- Docker контейнеры (app, postgres, redis, nginx)
- Docker volumes (после создания бэкапа)
- node_modules/
- src/ (TypeScript код)
- package.json, tsconfig.json
- dist/, build/

### 📦 Будет установлено
- Python 3.11
- python3.11-venv, python3.11-dev
- Poetry (менеджер зависимостей)
- build-essential, libpq-dev (для компиляции)

### 📁 Новая структура директорий
```
/opt/sigmatrade/
├── app/                    # Python код
│   ├── bot/               # Telegram бот
│   │   ├── handlers/
│   │   ├── keyboards/
│   │   ├── middlewares/
│   │   └── states/
│   ├── services/          # Бизнес-логика
│   │   ├── blockchain/
│   │   ├── notification/
│   │   └── payment/
│   ├── database/          # База данных
│   │   ├── entities/
│   │   └── migrations/
│   ├── utils/             # Утилиты
│   └── config/            # Конфигурация
├── logs/                  # Логи
├── data/                  # Данные
├── backups/               # Бэкапы
└── PYTHON_DEPLOYMENT_NEXT_STEPS.md  # Инструкции
```

---

## 🔐 Что нужно подготовить

### 1. Переменные окружения (.env)

Скопируйте эти значения из текущего `.env` файла:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_token_here

# База данных
DB_HOST=localhost  # или IP PostgreSQL
DB_PORT=5432
DB_USERNAME=botuser
DB_PASSWORD=your_password
DB_DATABASE=sigmatrade

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # если установлен

# Blockchain (QuickNode)
QUICKNODE_HTTPS_URL=https://your-quicknode.com/...
QUICKNODE_WSS_URL=wss://your-quicknode.com/...
BSC_CHAIN_ID=56
BSC_START_BLOCK=your_block_number

# Кошельки
SYSTEM_WALLET_ADDRESS=0x...
PAYOUT_WALLET_ADDRESS=0x...
USDT_CONTRACT=0x55d398326f99059fF775485246999027B3197955

# Админ
ADMIN_MASTER_KEY=your_master_key

# Безопасность
ENCRYPTION_KEY=your_encryption_key
SESSION_KEY=your_session_key
```

### 2. GitHub Repository

Убедитесь, что Python версия загружена в ветку `Migration-to-Python`:

```bash
# Проверить ветку локально
git branch -a | grep Migration-to-Python

# Если ветка существует на удаленном репозитории
git ls-remote --heads origin Migration-to-Python
```

---

## 🎯 Пошаговая инструкция

### Этап 1: Подготовка (локально на Windows)

```powershell
# 1. Перейти в директорию проекта
cd C:\Users\konfu\Desktop\sigmatradebot

# 2. Проверить что скрипты на месте
ls cleanup_server.ps1, server_cleanup.sh

# 3. Запустить автоматическую очистку
.\cleanup_server.ps1

# Скрипт спросит подтверждение перед критичными операциями
# Внимательно читайте вывод!
```

### Этап 2: Проверка результата

После выполнения скрипта подключитесь к серверу:

```powershell
gcloud compute ssh sigmatrade-20251108-210354 --zone=europe-north1-a
```

Проверьте:

```bash
# 1. Python установлен
python3.11 --version
# Ожидается: Python 3.11.x

# 2. Poetry установлен
poetry --version
# Ожидается: Poetry (version x.x.x)

# 3. Бэкап создан
ls -la /opt/sigmatrade/backups/
# Должна быть папка typescript_final_YYYYMMDD_HHMMSS/

# 4. Директории созданы
ls -la /opt/sigmatrade/app/
# Должны быть: bot/, services/, database/, utils/, config/

# 5. Docker контейнеры остановлены
docker ps -a
# Не должно быть запущенных контейнеров sigmatrade_*

# 6. Свободное место
df -h
# Должно быть минимум 5-6 GB свободно
```

### Этап 3: Развертывание Python версии

На сервере выполните:

```bash
cd /opt/sigmatrade

# 1. Клонировать Python версию
# ЗАМЕНИТЕ yourusername на ваш GitHub username!
git clone -b Migration-to-Python https://github.com/yourusername/sigmatradebot.git temp_repo
mv temp_repo/* temp_repo/.* . 2>/dev/null || true
rm -rf temp_repo

# 2. Создать .env файл
cp .env.example .env
nano .env
# Вставьте все переменные окружения из раздела "Что нужно подготовить"

# 3. Установить зависимости
poetry install --no-dev

# 4. Создать базу данных (если используете Docker)
docker-compose up -d postgres redis

# Подождать запуска (30 сек)
sleep 30

# 5. Применить миграции
poetry run alembic upgrade head

# 6. Запустить бота
poetry run python -m app.main

# Или через Docker (если docker-compose.yml готов)
docker-compose up -d app
```

### Этап 4: Проверка работоспособности

```bash
# 1. Проверить логи
tail -f logs/app.log

# Должны быть сообщения:
# ✅ Database connected
# ✅ Redis connected
# ✅ Bot started successfully

# 2. Проверить процесс
ps aux | grep python

# 3. Проверить Docker (если используется)
docker ps
# Должны работать: postgres, redis, app

# 4. Отправить /start боту в Telegram
# Бот должен ответить приветственным сообщением

# 5. Проверить админ панель
# /admin_login -> ввести master key -> /admin_panel
# Должна открыться админ панель

# 6. Проверить метрики (если реализовано)
curl http://localhost:8000/metrics

# 7. Проверить health check (если реализовано)
curl http://localhost:8000/health
```

---

## 🔄 Откат к TypeScript (если что-то пошло не так)

Если Python версия не работает, можно вернуться к TypeScript:

```bash
cd /opt/sigmatrade

# 1. Найти последний бэкап
BACKUP_DIR=$(ls -td backups/typescript_final_* | head -1)
echo "Восстанавливаем из: $BACKUP_DIR"

# 2. Остановить Python версию
docker-compose down 2>/dev/null || true
pkill -9 python

# 3. Восстановить код TypeScript
tar -xzf $BACKUP_DIR/typescript_code_*.tar.gz

# 4. Восстановить базу данных
docker-compose up -d postgres
sleep 10
docker exec -i sigmatrade_postgres psql -U botuser < $BACKUP_DIR/postgres_full_dump.sql

# 5. Восстановить Redis
docker cp $BACKUP_DIR/redis_dump.rdb sigmatrade_redis:/data/dump.rdb
docker restart sigmatrade_redis

# 6. Запустить TypeScript версию
npm ci --production
docker-compose up -d app

# Проверить
docker ps
docker logs sigmatrade_app
```

**Время отката:** 5-7 минут

---

## 📊 Чеклист миграции

### Перед миграцией
- [ ] Убедиться что сервер работает
- [ ] Проверить что есть минимум 10GB свободного места
- [ ] Сохранить все переменные окружения из .env
- [ ] Убедиться что Python код в ветке `Migration-to-Python`
- [ ] Предупредить пользователей о downtime (если нужно)

### Во время миграции
- [ ] Запустить `cleanup_server.ps1`
- [ ] Дождаться завершения (5-10 минут)
- [ ] Проверить что бэкап создан
- [ ] Проверить что Python установлен
- [ ] Проверить что директории созданы

### После миграции
- [ ] Склонировать Python код
- [ ] Настроить .env файл
- [ ] Установить зависимости
- [ ] Применить миграции БД
- [ ] Запустить бота
- [ ] Проверить логи (нет ошибок)
- [ ] Отправить /start боту (работает)
- [ ] Проверить админ панель (работает)
- [ ] Проверить обработку депозитов (работает)
- [ ] Мониторить систему 24 часа

### Финализация
- [ ] Настроить автозапуск (systemd или PM2)
- [ ] Настроить логротацию
- [ ] Настроить мониторинг (если есть)
- [ ] Настроить бэкапы (cron)
- [ ] Обновить документацию
- [ ] Удалить старые бэкапы TypeScript (через неделю)

---

## 🆘 Помощь и поддержка

### Проблемы с подключением к серверу

```powershell
# Проверить статус сервера
gcloud compute instances list --filter="name=sigmatrade"

# Запустить сервер (если остановлен)
gcloud compute instances start sigmatrade-20251108-210354 --zone=europe-north1-a

# Проверить firewall rules
gcloud compute firewall-rules list --filter="name~sigmatrade"
```

### Проблемы с Python

```bash
# Проверить версию Python
python3.11 --version

# Переустановить Python (если нужно)
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Проверить Poetry
poetry --version

# Переустановить Poetry (если нужно)
curl -sSL https://install.python-poetry.org | python3.11 -
```

### Проблемы с Docker

```bash
# Проверить Docker
docker --version
docker compose version

# Очистить Docker полностью
docker system prune -af --volumes

# Перезапустить Docker
sudo systemctl restart docker
```

### Проблемы с БД

```bash
# Проверить что PostgreSQL работает
docker ps | grep postgres

# Подключиться к БД
docker exec -it sigmatrade_postgres psql -U botuser -d sigmatrade

# Проверить таблицы
\dt

# Проверить пользователей
SELECT COUNT(*) FROM users;

# Выход
\q
```

### Логи для диагностики

```bash
# Логи приложения
tail -100 logs/app.log

# Логи Docker
docker logs sigmatrade_app --tail 100

# Системные логи
sudo journalctl -u docker -n 100

# Логи PostgreSQL
docker logs sigmatrade_postgres --tail 50
```

---

## 📚 Документация

- [Python Migration README](./PYTHON_MIGRATION_README.md)
- [Migration Documentation Part 1-5](./CLOUD_CODE_PYTHON_MIGRATION*.md)
- [Architecture Documentation](./docs/architecture/ARCHITECTURE.md)
- [Deployment Guide](./docs/deployment/DEPLOYMENT_GUIDE.md)

---

## 🎯 Итоговый статус

После завершения миграции вы должны иметь:

- ✅ Работающую Python версию бота
- ✅ Полный бэкап TypeScript версии
- ✅ PostgreSQL и Redis в Docker контейнерах
- ✅ Логирование и мониторинг
- ✅ Автоматические бэкапы
- ✅ Graceful shutdown
- ✅ Health checks

**Estimated Total Time:** 30-60 минут (включая проверки)
**Estimated Downtime:** 15-20 минут (только время остановки бота)

---

**Создано:** 2025-11-14  
**Версия:** 1.0  
**Автор:** Claude AI Assistant

**Удачи с миграцией! 🚀**

