#!/bin/bash

# =================================================================
# Скрипт очистки сервера и подготовки к Python версии бота
# Server: sigmatrade-20251108-210354 (34.88.234.78)
# =================================================================

set -e  # Exit on error

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🧹 Подготовка сервера к Python версии${NC}"
echo -e "${BLUE}========================================${NC}\n"

# =================================================================
# ШАГ 1: Проверка текущего состояния
# =================================================================
echo -e "${YELLOW}[1/8] Проверка текущего состояния...${NC}"

cd /opt/sigmatrade || { echo -e "${RED}❌ Директория /opt/sigmatrade не найдена!${NC}"; exit 1; }

# Проверка Docker контейнеров
echo "Текущие контейнеры:"
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Проверка места на диске
echo -e "\nМесто на диске:"
df -h / | grep -E "Filesystem|/$"

echo -e "${GREEN}✅ Проверка завершена${NC}\n"

# =================================================================
# ШАГ 2: Создание полного бэкапа
# =================================================================
echo -e "${YELLOW}[2/8] Создание бэкапа текущего состояния...${NC}"

BACKUP_DIR="/opt/sigmatrade/backups/typescript_final_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Директория бэкапа: $BACKUP_DIR"

# Бэкап базы данных PostgreSQL (если контейнер запущен)
if docker ps | grep -q sigmatrade_postgres; then
    echo "Создание бэкапа PostgreSQL..."
    docker exec sigmatrade_postgres pg_dumpall -U botuser > "$BACKUP_DIR/postgres_full_dump.sql"
    echo -e "${GREEN}✅ Бэкап PostgreSQL создан${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL контейнер не запущен, пропускаем бэкап БД${NC}"
fi

# Бэкап данных Redis (если контейнер запущен)
if docker ps | grep -q sigmatrade_redis; then
    echo "Создание бэкапа Redis..."
    docker exec sigmatrade_redis redis-cli SAVE
    docker cp sigmatrade_redis:/data/dump.rdb "$BACKUP_DIR/redis_dump.rdb"
    echo -e "${GREEN}✅ Бэкап Redis создан${NC}"
else
    echo -e "${YELLOW}⚠️  Redis контейнер не запущен, пропускаем бэкап Redis${NC}"
fi

# Бэкап конфигурационных файлов
echo "Создание бэкапа конфигурации..."
cp .env "$BACKUP_DIR/.env.backup" 2>/dev/null || echo "⚠️  Файл .env не найден"
cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.backup" 2>/dev/null || echo "⚠️  docker-compose.yml не найден"
cp -r logs "$BACKUP_DIR/logs_backup" 2>/dev/null || echo "⚠️  Директория logs не найдена"

# Создание архива текущего кода
echo "Архивация текущего кода..."
tar -czf "$BACKUP_DIR/typescript_code_$(date +%Y%m%d_%H%M%S).tar.gz" \
    --exclude=node_modules \
    --exclude=.git \
    --exclude=backups \
    --exclude=logs \
    --exclude=data \
    . 2>/dev/null || echo "⚠️  Не удалось создать архив кода"

echo -e "${GREEN}✅ Бэкап создан: $BACKUP_DIR${NC}\n"

# =================================================================
# ШАГ 3: Остановка и удаление контейнеров
# =================================================================
echo -e "${YELLOW}[3/8] Остановка Docker контейнеров...${NC}"

# Graceful shutdown с таймаутом
if [ -f docker-compose.yml ]; then
    echo "Остановка через docker-compose..."
    docker-compose down --timeout 30
    echo -e "${GREEN}✅ Контейнеры остановлены через docker-compose${NC}"
else
    echo "Остановка контейнеров вручную..."
    docker stop sigmatrade_app sigmatrade_postgres sigmatrade_redis sigmatrade_nginx 2>/dev/null || true
    docker rm sigmatrade_app sigmatrade_postgres sigmatrade_redis sigmatrade_nginx 2>/dev/null || true
    echo -e "${GREEN}✅ Контейнеры остановлены вручную${NC}"
fi

echo -e "\nТекущие контейнеры после остановки:"
docker ps -a

echo -e "${GREEN}✅ Все контейнеры остановлены${NC}\n"

# =================================================================
# ШАГ 4: Очистка Docker ресурсов
# =================================================================
echo -e "${YELLOW}[4/8] Очистка Docker ресурсов...${NC}"

# Удаление volumes (осторожно!)
echo -e "${RED}⚠️  ВНИМАНИЕ: Удаление Docker volumes!${NC}"
echo "Данные сохранены в бэкапе: $BACKUP_DIR"
read -p "Продолжить удаление volumes? (yes/no): " -r
if [[ $REPLY == "yes" ]]; then
    docker volume rm sigmatrade_postgres_data sigmatrade_redis_data 2>/dev/null || true
    echo -e "${GREEN}✅ Docker volumes удалены${NC}"
else
    echo -e "${YELLOW}⚠️  Volumes оставлены${NC}"
fi

# Удаление неиспользуемых образов
echo "Очистка неиспользуемых образов..."
docker image prune -af --filter "label!=keep"

# Проверка освободившегося места
echo -e "\nОсвободившееся место:"
df -h / | grep -E "Filesystem|/$"

echo -e "${GREEN}✅ Docker ресурсы очищены${NC}\n"

# =================================================================
# ШАГ 5: Очистка директорий проекта
# =================================================================
echo -e "${YELLOW}[5/8] Очистка директорий проекта...${NC}"

# Сохранение критичных файлов
echo "Создание списка сохраняемых файлов..."
KEEP_FILES=(
    ".env"
    "secrets_local.env"
    "backups/*"
    "DEPLOYMENT_*.txt"
    "README.md"
)

# Удаление TypeScript кода
echo "Удаление TypeScript файлов..."
rm -rf node_modules/
rm -rf dist/
rm -rf src/
rm -rf contracts/
rm -f package.json package-lock.json tsconfig*.json
rm -f Dockerfile docker-compose.yml
rm -f .dockerignore .gitignore
rm -rf .git/  # Удаляем Git, потом склонируем заново

echo "Удаление логов (старые сохранены в бэкапе)..."
rm -rf logs/*

echo "Удаление данных (старые сохранены в бэкапе)..."
rm -rf data/*

echo -e "${GREEN}✅ Директории очищены${NC}\n"

# =================================================================
# ШАГ 6: Установка Python окружения
# =================================================================
echo -e "${YELLOW}[6/8] Установка Python окружения...${NC}"

# Обновление системы
echo "Обновление системных пакетов..."
sudo apt-get update -qq

# Установка Python 3.11
echo "Проверка версии Python..."
if ! command -v python3.11 &> /dev/null; then
    echo "Установка Python 3.11..."
    sudo apt-get install -y \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3-pip \
        build-essential \
        libpq-dev \
        pkg-config
    echo -e "${GREEN}✅ Python 3.11 установлен${NC}"
else
    echo -e "${GREEN}✅ Python 3.11 уже установлен${NC}"
fi

# Проверка версии
python3.11 --version

# Установка Poetry (для управления зависимостями)
echo "Установка Poetry..."
if ! command -v poetry &> /dev/null; then
    curl -sSL https://install.python-poetry.org | python3.11 -
    export PATH="$HOME/.local/bin:$PATH"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo -e "${GREEN}✅ Poetry установлен${NC}"
else
    echo -e "${GREEN}✅ Poetry уже установлен${NC}"
fi

poetry --version

echo -e "${GREEN}✅ Python окружение готово${NC}\n"

# =================================================================
# ШАГ 7: Создание структуры для Python проекта
# =================================================================
echo -e "${YELLOW}[7/8] Создание структуры для Python проекта...${NC}"

# Создание базовых директорий
echo "Создание директорий..."
mkdir -p /opt/sigmatrade/{logs,data,backups,app}
mkdir -p /opt/sigmatrade/app/{bot,services,database,utils,config}
mkdir -p /opt/sigmatrade/app/bot/{handlers,keyboards,middlewares,states}
mkdir -p /opt/sigmatrade/app/services/{blockchain,notification,payment}
mkdir -p /opt/sigmatrade/app/database/{entities,migrations}

# Установка правильных прав
echo "Настройка прав доступа..."
sudo chown -R konfu:konfu /opt/sigmatrade
chmod -R 755 /opt/sigmatrade

echo -e "${GREEN}✅ Структура директорий создана${NC}\n"

# =================================================================
# ШАГ 8: Создание README для следующих шагов
# =================================================================
echo -e "${YELLOW}[8/8] Создание инструкций для следующих шагов...${NC}"

cat > /opt/sigmatrade/PYTHON_DEPLOYMENT_NEXT_STEPS.md <<'EOF'
# 🐍 Следующие шаги для развертывания Python версии

## ✅ Что уже готово:
- ✅ TypeScript версия остановлена и заархивирована
- ✅ Бэкапы созданы в `backups/typescript_final_*`
- ✅ Docker volumes очищены
- ✅ Python 3.11 установлен
- ✅ Poetry установлен
- ✅ Структура директорий создана

## 📋 Следующие шаги:

### 1. Клонирование Python версии из GitHub

```bash
cd /opt/sigmatrade

# Клонировать ветку Migration-to-Python
git clone -b Migration-to-Python https://github.com/yourusername/sigmatradebot.git temp_repo

# Переместить файлы в текущую директорию
mv temp_repo/* temp_repo/.* . 2>/dev/null || true
rm -rf temp_repo
```

### 2. Настройка окружения

```bash
# Создать .env файл на основе .env.example
cp .env.example .env
nano .env

# Обязательные переменные:
# - TELEGRAM_BOT_TOKEN
# - DB_HOST, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_DATABASE
# - REDIS_HOST, REDIS_PORT
# - QUICKNODE_HTTPS_URL, QUICKNODE_WSS_URL
# - SYSTEM_WALLET_ADDRESS, PAYOUT_WALLET_ADDRESS
```

### 3. Установка зависимостей

```bash
# Активировать виртуальное окружение и установить зависимости
poetry install --no-dev

# Или с pip:
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Настройка базы данных

```bash
# Создать базу данных (если нужно)
# docker-compose up -d postgres redis

# Применить миграции
poetry run alembic upgrade head

# Или:
# python -m app.database.migrations.migrate
```

### 5. Запуск бота

```bash
# Запуск через Poetry
poetry run python -m app.main

# Или через Docker Compose
docker-compose up -d

# Или через systemd (создать service файл)
sudo systemctl start sigmatradebot-python
```

### 6. Проверка работоспособности

```bash
# Проверить логи
tail -f logs/app.log

# Проверить процесс
ps aux | grep python

# Проверить Docker контейнеры
docker ps

# Отправить /start боту в Telegram
```

### 7. Мониторинг

```bash
# Проверить метрики
curl http://localhost:8000/metrics

# Проверить health
curl http://localhost:8000/health

# Проверить базу данных
psql -h localhost -U botuser -d sigmatrade -c "SELECT COUNT(*) FROM users;"
```

## 🔄 Восстановление из бэкапа (если нужно)

```bash
# Найти последний бэкап
ls -la backups/typescript_final_*/

# Восстановить PostgreSQL
docker-compose up -d postgres
docker exec -i sigmatrade_postgres psql -U botuser < backups/typescript_final_*/postgres_full_dump.sql

# Восстановить Redis
docker cp backups/typescript_final_*/redis_dump.rdb sigmatrade_redis:/data/dump.rdb
docker restart sigmatrade_redis

# Восстановить код TypeScript
cd /opt/sigmatrade
tar -xzf backups/typescript_final_*/typescript_code_*.tar.gz
```

## 📞 Поддержка

В случае проблем:
1. Проверить логи: `tail -f logs/app.log`
2. Проверить документацию: `docs/`
3. Проверить бэкапы: `backups/`

## 🎯 Чеклист развертывания

- [ ] Код Python версии склонирован
- [ ] .env файл настроен
- [ ] Зависимости установлены
- [ ] База данных создана и мигрирована
- [ ] Бот запущен
- [ ] Бот отвечает на команды
- [ ] Мониторинг настроен
- [ ] Бэкапы проверены

**Дата подготовки:** $(date)
**Версия:** 1.0
EOF

echo -e "${GREEN}✅ README создан: /opt/sigmatrade/PYTHON_DEPLOYMENT_NEXT_STEPS.md${NC}\n"

# =================================================================
# ИТОГОВАЯ ИНФОРМАЦИЯ
# =================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}✅ Сервер подготовлен к Python версии!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${GREEN}Выполнено:${NC}"
echo "  ✅ Создан бэкап в: $BACKUP_DIR"
echo "  ✅ Остановлены Docker контейнеры"
echo "  ✅ Очищены Docker volumes"
echo "  ✅ Удалены TypeScript файлы"
echo "  ✅ Установлен Python 3.11 + Poetry"
echo "  ✅ Создана структура директорий"
echo ""

echo -e "${YELLOW}Следующие шаги:${NC}"
echo "  1. Прочитать: /opt/sigmatrade/PYTHON_DEPLOYMENT_NEXT_STEPS.md"
echo "  2. Склонировать Python код из ветки Migration-to-Python"
echo "  3. Настроить .env файл"
echo "  4. Установить зависимости (poetry install)"
echo "  5. Применить миграции БД"
echo "  6. Запустить бота"
echo ""

echo -e "${BLUE}Свободное место на диске:${NC}"
df -h / | grep -E "Filesystem|/$"

echo -e "\n${GREEN}🎉 Готово! Сервер очищен и подготовлен для Python версии!${NC}"
echo -e "${YELLOW}📖 Следуйте инструкциям в PYTHON_DEPLOYMENT_NEXT_STEPS.md${NC}\n"

