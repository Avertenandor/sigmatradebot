# 🎯 ПРЯМАЯ ИНСТРУКЦИЯ ДЛЯ CURSOR IDE

**Скопируйте этот текст в Cursor Chat и нажмите Enter**

---

```
Привет! Мне нужна твоя помощь с проектом SigmaTrade Bot (Python версия).

ПРОЕКТ:
- Telegram DeFi бот на Python 3.11+, aiogram 3.x, PostgreSQL, Docker
- Статус: 98% готов к production, нужна финальная доработка
- Директория: C:\Users\konfu\Desktop\sigmatradebot
- Документация: docs/cursor/

ЗАДАЧА:
Подготовить бот к production деплою через улучшение валидации, добавление health checks и финальную проверку всех компонентов.

ЧТО НУЖНО СДЕЛАТЬ (P0 - Критично):

1. **scripts/validate-env.py** - Добавить валидацию форматов
   - Функция validate_telegram_token() - проверка формата
   - Функция validate_wallet_address() - проверка 0x и длины
   - Функция validate_database_url() - проверка драйвера
   - Использовать эти функции в validate_env()

2. **scripts/health-check.sh** - СОЗДАТЬ НОВЫЙ скрипт
   - Проверка Docker контейнеров (running/stopped)
   - Проверка PostgreSQL (pg_isready)
   - Проверка Redis (redis-cli ping)
   - Проверка логов на ошибки (последние 100 строк)
   - Проверка места на диске (df -h)

3. **app/config/settings.py** - Добавить Pydantic валидаторы
   - @field_validator для telegram_bot_token
   - @field_validator для wallet_address и system_wallet_address
   - @field_validator для database_url
   - @field_validator для secret_key и encryption_key
   - @model_validator для production (DEBUG=False)

4. **docker-entrypoint.sh** - Улучшить обработку
   - Функция wait_for_postgres()
   - Функция wait_for_redis()
   - Проверка DATABASE_URL и TELEGRAM_BOT_TOKEN
   - Вызвать wait функции перед запуском
   - Улучшенное логирование для каждой команды

5. **bot/main.py** - Добавить error handler
   - Async функция error_handler(event: ErrorEvent, bot: Bot)
   - Логирование с полным traceback
   - Уведомления первым 3 админам
   - Регистрация через dp.errors.register()

6. **.env.example** - Обновить комментарии
   - Предупреждения в начале файла
   - Описание каждой переменной
   - Инструкции по генерации ключей (openssl rand -hex 32)
   - Примеры правильных форматов

ДЕТАЛИ И ПРИМЕРЫ КОДА:
Все детали в docs/cursor/CURSOR_INSTRUCTIONS_SERVER_CLEANUP.md
Быстрый старт в docs/cursor/QUICK_START_GUIDE.md

ВАЖНО:
- Не упрощай код
- Добавляй полную функциональность
- Следуй best practices
- Проверяй синтаксис

После выполнения каждой задачи покажи:
1. Что было изменено
2. Код который был добавлен
3. Команду для проверки

Готов начать? Начни с задачи #1 (validate-env.py)
```

---

## 📋 АЛЬТЕРНАТИВНЫЕ ПРОМПТЫ

### Промпт #1: Для быстрого выполнения

```
Помоги подготовить SigmaTrade Bot к production.

Проект: C:\Users\konfu\Desktop\sigmatradebot
Задача: Выполнить все изменения из docs/cursor/QUICK_START_GUIDE.md

Действуй по шагам:
1. Прочитай файл docs/cursor/QUICK_START_GUIDE.md
2. Выполни все 5 задач последовательно
3. После каждой задачи покажи что изменилось
4. В конце дай команду для проверки

Начни сейчас!
```

---

### Промпт #2: Для конкретной задачи

```
Мне нужно улучшить валидацию в scripts/validate-env.py

Проект: C:\Users\konfu\Desktop\sigmatradebot

Добавь 3 функции:
1. validate_telegram_token() - проверка формата ^\d+:[A-Za-z0-9_-]{35}$
2. validate_wallet_address() - проверка 0x и длины 42
3. validate_database_url() - проверка postgresql+asyncpg://

Используй их в функции validate_env() при проверке переменных.

Детали в docs/cursor/CURSOR_INSTRUCTIONS_SERVER_CLEANUP.md (Задача 1)

Покажи полный код функций и как их интегрировать.
```

---

### Промпт #3: Создание health-check.sh

```
Создай новый файл scripts/health-check.sh

Требования:
- Bash скрипт с проверками здоровья системы
- Проверки: Docker, PostgreSQL, Redis, логи, диск
- Цветной вывод (GREEN для OK, RED для ошибок)
- Exit code 1 при любой ошибке

Детали в docs/cursor/CURSOR_INSTRUCTIONS_SERVER_CLEANUP.md (Задача 2)

После создания:
1. Покажи весь код
2. Дай команду chmod +x
3. Дай команду для теста
```

---

### Промпт #4: Для добавления валидаторов в settings.py

```
Добавь Pydantic валидаторы в app/config/settings.py

Нужны валидаторы:
1. @field_validator для telegram_bot_token
2. @field_validator для wallet_address и system_wallet_address  
3. @field_validator для database_url
4. @field_validator для secret_key и encryption_key
5. @model_validator для production (проверка DEBUG)

Детали в docs/cursor/CURSOR_INSTRUCTIONS_SERVER_CLEANUP.md (Задача 3)

Покажи:
1. Импорты которые нужно добавить
2. Все валидаторы с кодом
3. Где их разместить в классе Settings
```

---

### Промпт #5: Для улучшения docker-entrypoint.sh

```
Улучши docker-entrypoint.sh

Добавь:
1. Функцию wait_for_postgres() - ожидание через nc -z
2. Функцию wait_for_redis() - ожидание через nc -z
3. Проверки DATABASE_URL и TELEGRAM_BOT_TOKEN
4. Вызовы wait функций перед запуском команд
5. Логирование для каждого этапа

Детали в docs/cursor/CURSOR_INSTRUCTIONS_SERVER_CLEANUP.md (Задача 4)

Покажи полный обновленный файл.
```

---

### Промпт #6: Для error handler в bot/main.py

```
Добавь глобальный error handler в bot/main.py

Требования:
- Async функция error_handler(event: ErrorEvent, bot: Bot)
- Логирование с loguru (полный traceback)
- Уведомления первым 3 админам через send_message
- HTML формат сообщения с типом ошибки
- Регистрация через dp.errors.register(error_handler)

Детали в docs/cursor/CURSOR_INSTRUCTIONS_SERVER_CLEANUP.md (Задача 5)

Покажи:
1. Импорты
2. Функцию error_handler
3. Где зарегистрировать в main()
```

---

## 💡 КАК ИСПОЛЬЗОВАТЬ

1. **Скопируй один из промптов выше**
2. **Вставь в Cursor Chat**
3. **Нажми Enter**
4. **Следуй инструкциям Cursor**

---

## ✅ ПОСЛЕ ВЫПОЛНЕНИЯ

Проверь работу:

```bash
# Валидация
python3 scripts/validate-env.py

# Health check
chmod +x scripts/health-check.sh
./scripts/health-check.sh

# Settings
python3 -c "from app.config.settings import Settings; print('OK')"

# Docker
docker build -f Dockerfile.python -t sigmatrade:test .

# Тесты
pytest tests/test_imports.py -v
```

---

Коммит:

```bash
git add .
git commit -m "chore: production deployment preparation

- Enhanced validate-env.py with format validators
- Added health-check.sh for monitoring  
- Improved settings.py with Pydantic validators
- Better error handling in bot/main.py
- Enhanced docker-entrypoint.sh with wait functions
- Updated .env.example with detailed comments"

git push origin claude/sigmatradebot-python-migration-01UUhWd7yPartmZdGxtPAFLo
```

---

**Готово! Выбери промпт и начинай работу! 🚀**
