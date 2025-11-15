# ✅ Production Deploy Checklist

**Дата:** 2025-01-15  
**Версия:** Python Migration v1.0  
**Статус готовности:** 🟢 95%

---

## ✅ ПРЕДВАРИТЕЛЬНАЯ ПРОВЕРКА

### Код готов
- [x] Все настройки добавлены в Settings
- [x] BlockchainService полностью реализован
- [x] Все handlers используют правильные настройки
- [x] Инициализация BlockchainService во всех точках входа
- [x] Async обертки для синхронных Web3 вызовов
- [x] .env.example создан
- [x] Deploy скрипт создан
- [x] Обработка ошибок миграций улучшена

### Документация готова
- [x] DEPLOYMENT.md обновлен
- [x] Инструкции по backup добавлены
- [x] PRODUCTION_READINESS_REPORT.md обновлен

---

## 📋 ШАГИ ДЛЯ ДЕПЛОЯ

### 1. Подготовка сервера

```bash
# 1.1 Обновить систему
sudo apt update && sudo apt upgrade -y

# 1.2 Установить Docker и Docker Compose
sudo apt install docker.io docker-compose -y
sudo systemctl enable docker
sudo systemctl start docker

# 1.3 Установить PostgreSQL (если не используется Docker)
sudo apt install postgresql postgresql-contrib -y

# 1.4 Установить Redis (если не используется Docker)
sudo apt install redis-server -y
sudo systemctl enable redis
sudo systemctl start redis
```

### 2. Настройка переменных окружения

```bash
# 2.1 Скопировать .env.example
cd /opt/sigmatradebot
cp .env.example .env

# 2.2 Отредактировать .env
nano .env

# 2.3 Заполнить все обязательные переменные:
# - TELEGRAM_BOT_TOKEN
# - DATABASE_URL
# - WALLET_PRIVATE_KEY
# - WALLET_ADDRESS
# - USDT_CONTRACT_ADDRESS
# - RPC_URL
# - SYSTEM_WALLET_ADDRESS
# - REDIS_HOST, REDIS_PORT
# - SECRET_KEY, ENCRYPTION_KEY
# - ADMIN_TELEGRAM_IDS

# 2.4 Установить права доступа
chmod 600 .env
```

### 3. Сборка и запуск Docker контейнеров

```bash
# 3.1 Перейти в директорию проекта
cd /opt/sigmatradebot

# 3.2 Собрать образы
docker-compose -f docker-compose.python.yml build

# 3.3 Запустить сервисы
docker-compose -f docker-compose.python.yml up -d

# 3.4 Проверить статус
docker-compose -f docker-compose.python.yml ps

# 3.5 Проверить логи
docker-compose -f docker-compose.python.yml logs -f bot
```

### 4. Проверка работы

```bash
# 4.1 Проверить логи бота
docker-compose -f docker-compose.python.yml logs bot | tail -50

# 4.2 Проверить логи worker
docker-compose -f docker-compose.python.yml logs worker | tail -50

# 4.3 Проверить логи scheduler
docker-compose -f docker-compose.python.yml logs scheduler | tail -50

# 4.4 Проверить подключение к базе данных
docker exec sigmatrade-postgres psql -U sigmatrade -d sigmatrade -c "SELECT COUNT(*) FROM users;"

# 4.5 Проверить подключение к Redis
docker exec sigmatrade-redis redis-cli ping
```

### 5. Тестирование функциональности

- [ ] Отправить /start боту в Telegram
- [ ] Проверить регистрацию нового пользователя
- [ ] Проверить главное меню
- [ ] Проверить депозит (создание депозита)
- [ ] Проверить вывод (создание запроса на вывод)
- [ ] Проверить админ панель (для админа)
- [ ] Проверить мониторинг депозитов (logs worker)

### 6. Настройка backup

```bash
# 6.1 Сделать скрипт исполняемым
chmod +x /opt/sigmatradebot/scripts/backup-production.sh

# 6.2 Протестировать backup вручную
/opt/sigmatradebot/scripts/backup-production.sh

# 6.3 Настроить cron (ежедневно в 3:00)
(crontab -l 2>/dev/null; echo "0 3 * * * cd /opt/sigmatradebot && ./scripts/backup-production.sh >> /var/log/sigmatrade-backup.log 2>&1") | crontab -

# 6.4 Проверить crontab
crontab -l
```

### 7. Мониторинг (опционально)

```bash
# 7.1 Настроить логирование
# Логи уже настроены в docker-compose.python.yml

# 7.2 Настроить алерты (если нужно)
# Использовать scripts/notify_admin.py для критических событий
```

---

## 🔍 ПРОВЕРКА ПОСЛЕ ДЕПЛОЯ

### Критические проверки

- [ ] Бот отвечает на /start
- [ ] Регистрация пользователя работает
- [ ] BlockchainService инициализирован (проверить логи)
- [ ] База данных доступна
- [ ] Redis доступен
- [ ] Worker обрабатывает задачи
- [ ] Scheduler запущен

### Функциональные проверки

- [ ] Создание депозита
- [ ] Мониторинг депозитов работает
- [ ] Создание запроса на вывод
- [ ] Обработка payment retry
- [ ] Админ панель доступна
- [ ] Blacklist функционал работает

---

## 🚨 ОБРАТНАЯ СВЯЗЬ

Если что-то не работает:

1. **Проверить логи:**
   ```bash
   docker-compose -f docker-compose.python.yml logs -f
   ```

2. **Проверить переменные окружения:**
   ```bash
   docker exec sigmatrade-bot env | grep -E "TELEGRAM|DATABASE|WALLET|RPC"
   ```

3. **Проверить подключение к BSC:**
   - Проверить RPC_URL в .env
   - Проверить логи на ошибки подключения

4. **Проверить миграции:**
   ```bash
   docker exec sigmatrade-bot alembic current
   docker exec sigmatrade-bot alembic history
   ```

---

## ✅ ГОТОВО К PRODUCTION!

После выполнения всех шагов бот готов к работе в production.

**Время деплоя:** ~30-60 минут

