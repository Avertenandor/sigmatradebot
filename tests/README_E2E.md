# E2E Testing для Telegram бота

## Обзор

Система e2e тестирования для Telegram бота **без использования реального Telegram API**. Аналогично Selenium/Playwright для веб-сайтов, но для Telegram ботов.

## Технологии

- **pytest** - фреймворк для тестирования
- **pytest-asyncio** - поддержка асинхронных тестов
- **aiogram MemorySession** - мок Telegram Bot API
- **aiogram MockBot** - эмуляция бота без реальных запросов

## Преимущества

✅ **Быстро** - нет реальных API вызовов  
✅ **Надежно** - не зависит от внешних сервисов  
✅ **Изолированно** - каждый тест независим  
✅ **CI/CD готово** - работает в любом окружении  

## Установка

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

## Запуск тестов

### Все тесты
```bash
pytest
```

### Только E2E тесты
```bash
pytest tests/e2e/ -v
```

### С покрытием кода
```bash
pytest --cov=app --cov=bot --cov-report=html
```

### Конкретный тест
```bash
pytest tests/e2e/test_bot_e2e.py::test_start_command_flow -v
```

## Структура тестов

```
tests/
├── conftest.py              # Фикстуры pytest
├── e2e/
│   ├── test_bot_e2e.py      # Базовые e2e тесты
│   └── test_bot_with_client.py  # Тесты с BotTestClient
└── helpers/
    └── bot_test_client.py   # Высокоуровневый API для тестирования
```

## Примеры использования

### Простой тест

```python
@pytest.mark.asyncio
async def test_start_command(mock_bot, mock_dispatcher, test_user):
    """Test /start command."""
    client = await create_test_client(mock_bot, mock_dispatcher)
    
    # Отправляем команду
    await client.send_message("/start", user_id=123456789)
    
    # Проверяем результат
    assert len(client.get_sent_messages()) == 1
```

### Тест с несколькими шагами

```python
@pytest.mark.asyncio
async def test_deposit_flow(mock_bot, mock_dispatcher, test_user):
    """Test complete deposit flow."""
    client = await create_test_client(mock_bot, mock_dispatcher)
    
    # Шаг 1: Открываем меню депозита
    await client.send_callback("menu:deposit")
    
    # Шаг 2: Выбираем уровень
    await client.send_callback("deposit:level:1")
    
    # Шаг 3: Вводим сумму
    await client.send_message("100")
    
    # Шаг 4: Вводим хеш транзакции
    await client.send_message("0x123...")
    
    # Проверяем, что депозит создан
    assert len(client.get_received_updates()) == 4
```

### Тест с проверкой базы данных

```python
@pytest.mark.asyncio
async def test_user_registration(mock_bot, mock_dispatcher, db_session):
    """Test user registration flow."""
    client = await create_test_client(mock_bot, mock_dispatcher)
    
    # Регистрация нового пользователя
    await client.send_message("/start", user_id=999999999)
    await client.send_message("0xWalletAddress")
    await client.send_message("password123")
    await client.send_message("password123")
    
    # Проверяем в БД
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_telegram_id(999999999)
    
    assert user is not None
    assert user.wallet_address == "0xWalletAddress"
```

## Фикстуры

### `mock_bot`
Создает мок бота без реальных API вызовов.

### `mock_dispatcher`
Создает диспетчер с зарегистрированными handlers.

### `mock_user`
Создает тестового пользователя Telegram.

### `test_user`
Создает пользователя в тестовой БД.

### `test_admin`
Создает админа в тестовой БД.

### `db_session`
Создает сессию БД для тестов.

## BotTestClient

Высокоуровневый API для тестирования, аналогичный Selenium WebDriver:

```python
client = await create_test_client(mock_bot, mock_dispatcher)

# Отправка сообщения
await client.send_message("/start")

# Отправка callback
await client.send_callback("menu:deposit")

# Проверка ответа
await client.assert_response_contains("Welcome")

# История
messages = client.get_sent_messages()
updates = client.get_received_updates()
```

## Лучшие практики

1. **Изоляция** - каждый тест независим
2. **Очистка** - используйте фикстуры для очистки БД
3. **Читаемость** - используйте BotTestClient для сложных сценариев
4. **Покрытие** - стремитесь к 70%+ покрытию кода

## Отладка

### Запуск с выводом
```bash
pytest -v -s
```

### Запуск конкретного теста
```bash
pytest tests/e2e/test_bot_e2e.py::test_start_command_flow -v
```

### Просмотр покрытия
```bash
pytest --cov=app --cov-report=html
# Открыть htmlcov/index.html
```

## CI/CD

Тесты автоматически запускаются в CI/CD:

```yaml
# .github/workflows/test.yml
- name: Run E2E tests
  run: |
    pytest tests/e2e/ -v --cov=app --cov=bot
```

## Сравнение с реальным API

| Аспект | MockBot (наш подход) | Реальный API |
|--------|---------------------|--------------|
| Скорость | ⚡ Очень быстро | 🐌 Медленно |
| Надежность | ✅ Стабильно | ❌ Зависит от сети |
| Стоимость | 💰 Бесплатно | 💰 Может быть платно |
| CI/CD | ✅ Работает везде | ❌ Нужен токен |
| Отладка | ✅ Легко | ❌ Сложно |

## Дополнительные ресурсы

- [aiogram Testing Guide](https://docs.aiogram.dev/en/latest/dispatcher/testing.html)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

