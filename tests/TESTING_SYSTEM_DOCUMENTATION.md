# 🧪 Комплексная система тестирования SigmaTrade Bot

## 📋 Оглавление

- [Обзор](#обзор)
- [Архитектура тестирования](#архитектура-тестирования)
- [Типы тестов](#типы-тестов)
- [Покрытие по бизнес-ролям](#покрытие-по-бизнес-ролям)
- [Структура директорий](#структура-директорий)
- [Запуск тестов](#запуск-тестов)
- [Best Practices](#best-practices)

---

## 🎯 Обзор

Комплексная система тестирования для 100% покрытия всех компонентов, бизнес-процессов и сценариев SigmaTrade Bot.

**Цели:**
- ✅ 100% покрытие кода
- ✅ Все бизнес-роли (User, Admin, System)
- ✅ Все критические сценарии
- ✅ Безопасность и производительность
- ✅ Blockchain интеграция

**Статистика:**
- **21 модель** базы данных
- **11 основных сервисов**
- **3 бизнес-роли**
- **50+ критических сценариев**

---

## 🏗️ Архитектура тестирования

```
Pyramid Testing Model:
    /\
   /  \  E2E Tests (10-15%)
  /____\
 /      \  Integration Tests (25-30%)
/__________\  Unit Tests (55-65%)
```

### Уровни тестирования

1. **Unit Tests (55-65%)** - Изолированное тестирование компонентов
2. **Integration Tests (25-30%)** - Тестирование взаимодействия
3. **E2E Tests (10-15%)** - Сквозное тестирование сценариев
4. **Specialized Tests** - Безопасность, производительность, blockchain

---

## 📊 Типы тестов

### 1️⃣ Unit Tests
Изолированное тестирование отдельных компонентов с моками

**Покрытие:**
- ✅ Все модели (21 моделей)
- ✅ Все репозитории (20 репозиториев)
- ✅ Все сервисы (11 основных сервисов)
- ✅ Утилиты и хелперы

**Местоположение:** `tests/unit/`

### 2️⃣ Integration Tests
Тестирование взаимодействия компонентов

**Покрытие:**
- ✅ Database + Repository
- ✅ Service + Repository
- ✅ Service + External Services
- ✅ Workflow Integration

**Местоположение:** `tests/integration/`

### 3️⃣ E2E Tests
Сквозное тестирование полных бизнес-сценариев

**По ролям:**
- ✅ User scenarios (депозиты, выводы, рефералы)
- ✅ Admin scenarios (управление, одобрения)
- ✅ System scenarios (автоматика, ROI)

**Местоположение:** `tests/e2e/`

### 4️⃣ Blockchain Tests
Тестирование blockchain интеграции

**Покрытие:**
- ✅ Smart contract взаимодействие
- ✅ Deposit monitoring
- ✅ Withdrawal processing
- ✅ Transaction verification

**Местоположение:** `tests/blockchain/`

### 5️⃣ Security Tests
Тестирование безопасности

**Покрытие:**
- ✅ Authentication & Authorization
- ✅ Input validation
- ✅ SQL injection protection
- ✅ Rate limiting
- ✅ Financial password security

**Местоположение:** `tests/security/`

### 6️⃣ Performance Tests
Тестирование производительности

**Покрытие:**
- ✅ Load testing
- ✅ Stress testing
- ✅ Database query optimization
- ✅ Concurrent operations

**Местоположение:** `tests/performance/`

---

## 👥 Покрытие по бизнес-ролям

### 🧑 USER (Обычный пользователь)

**Основные сценарии:**
1. Регистрация и верификация
2. Депозиты (5 уровней: $10, $50, $100, $150, $300)
3. Получение ROI (2% daily до 500% cap)
4. Реферальная система (3 уровня: 3%, 2%, 5%)
5. Выводы средств
6. Восстановление финансового пароля
7. Поддержка (тикеты)
8. Просмотр транзакций и баланса

**Тесты:**
- ✅ User registration flow
- ✅ Deposit creation (все 5 уровней)
- ✅ ROI calculation and distribution
- ✅ Referral rewards (все 3 уровня)
- ✅ Withdrawal requests
- ✅ Financial password recovery
- ✅ Support ticket workflow
- ✅ Balance calculations
- ✅ Transaction history

### 👨‍💼 ADMIN (Администратор)

**Основные сценарии:**
1. Аутентификация админа
2. Управление пользователями (бан/разбан)
3. Одобрение выводов
4. Настройки системы (уровни депозитов, проценты)
5. Массовые рассылки
6. Просмотр статистики
7. Управление кошельками
8. Обработка апелляций
9. Ответы в поддержке

**Тесты:**
- ✅ Admin authentication
- ✅ User management (ban/unban)
- ✅ Withdrawal approvals
- ✅ System settings management
- ✅ Broadcast functionality
- ✅ Statistics and analytics
- ✅ Wallet management
- ✅ Appeal processing
- ✅ Support responses

### 🤖 SYSTEM (Автоматика)

**Основные сценарии:**
1. Ежедневная выплата ROI
2. Мониторинг депозитов в блокчейне
3. Обработка реферальных наград
4. Повторная отправка неудачных платежей
5. Повторная отправка уведомлений
6. Бэкапы базы данных
7. Очистка старых данных

**Тесты:**
- ✅ Daily ROI distribution
- ✅ Blockchain monitoring
- ✅ Referral rewards processing
- ✅ Payment retry mechanism
- ✅ Notification retry
- ✅ Automated backups
- ✅ Data cleanup jobs

---

## 📁 Структура директорий

```
tests/
├── unit/                           # Модульные тесты
│   ├── models/                     # Тесты моделей
│   │   ├── test_user.py           # User model
│   │   ├── test_deposit.py        # Deposit model
│   │   ├── test_transaction.py    # Transaction model
│   │   ├── test_referral.py       # Referral model
│   │   ├── test_admin.py          # Admin model
│   │   ├── test_support.py        # Support models
│   │   └── ...                    # Все 21 модель
│   ├── repositories/              # Тесты репозиториев
│   │   ├── test_user_repository.py
│   │   ├── test_deposit_repository.py
│   │   ├── test_transaction_repository.py
│   │   └── ...                    # Все 20 репозиториев
│   └── services/                  # Тесты сервисов
│       ├── test_user_service.py
│       ├── test_deposit_service.py
│       ├── test_withdrawal_service.py
│       ├── test_referral_service.py
│       ├── test_reward_service.py
│       ├── test_notification_service.py
│       ├── test_transaction_service.py
│       ├── test_support_service.py
│       ├── test_admin_service.py
│       ├── test_blacklist_service.py
│       └── ...                    # Все 11 сервисов
│
├── integration/                   # Интеграционные тесты
│   ├── workflows/                 # Бизнес-процессы
│   │   ├── test_deposit_workflow.py
│   │   ├── test_withdrawal_workflow.py
│   │   ├── test_referral_workflow.py
│   │   ├── test_roi_distribution.py
│   │   └── test_support_workflow.py
│   ├── test_database_integration.py
│   ├── test_blockchain_integration.py
│   └── test_notification_integration.py
│
├── e2e/                           # E2E тесты
│   ├── user_scenarios/            # Сценарии пользователя
│   │   ├── test_registration.py
│   │   ├── test_deposit_flow.py
│   │   ├── test_withdrawal_flow.py
│   │   ├── test_referral_flow.py
│   │   ├── test_roi_receiving.py
│   │   └── test_support_flow.py
│   ├── admin_scenarios/           # Сценарии админа
│   │   ├── test_admin_login.py
│   │   ├── test_user_management.py
│   │   ├── test_withdrawal_approval.py
│   │   ├── test_broadcast.py
│   │   └── test_settings_management.py
│   └── system_scenarios/          # Сценарии системы
│       ├── test_daily_roi.py
│       ├── test_deposit_monitoring.py
│       ├── test_payment_retry.py
│       └── test_notification_retry.py
│
├── blockchain/                    # Blockchain тесты
│   ├── test_deposit_monitoring.py
│   ├── test_withdrawal_processing.py
│   ├── test_transaction_verification.py
│   └── test_smart_contract_interaction.py
│
├── security/                      # Тесты безопасности
│   ├── test_authentication.py
│   ├── test_authorization.py
│   ├── test_input_validation.py
│   ├── test_sql_injection.py
│   ├── test_rate_limiting.py
│   └── test_financial_password.py
│
├── performance/                   # Тесты производительности
│   ├── test_load.py
│   ├── test_stress.py
│   ├── test_database_performance.py
│   └── test_concurrent_operations.py
│
├── fixtures/                      # Общие фикстуры
│   ├── database_fixtures.py
│   ├── user_fixtures.py
│   ├── deposit_fixtures.py
│   └── blockchain_fixtures.py
│
├── helpers/                       # Вспомогательные утилиты
│   ├── bot_test_client.py
│   ├── database_helper.py
│   ├── blockchain_mock.py
│   └── assertion_helpers.py
│
├── conftest.py                    # Pytest конфигурация
├── pytest.ini                     # Pytest настройки
├── TESTING_SYSTEM_DOCUMENTATION.md # Эта документация
└── TEST_COVERAGE_REPORT.md        # Отчет о покрытии
```

---

## 🚀 Запуск тестов

### Все тесты
```bash
pytest
```

### По типам
```bash
# Unit тесты
pytest tests/unit/

# Integration тесты
pytest tests/integration/

# E2E тесты
pytest tests/e2e/

# Blockchain тесты
pytest tests/blockchain/

# Security тесты
pytest tests/security/

# Performance тесты
pytest tests/performance/
```

### По ролям
```bash
# User scenarios
pytest tests/e2e/user_scenarios/

# Admin scenarios
pytest tests/e2e/admin_scenarios/

# System scenarios
pytest tests/e2e/system_scenarios/
```

### Конкретные компоненты
```bash
# Тесты моделей
pytest tests/unit/models/

# Тесты сервисов
pytest tests/unit/services/

# Тесты репозиториев
pytest tests/unit/repositories/
```

### С покрытием
```bash
# Генерация отчета
pytest --cov=app --cov=bot --cov-report=html

# Просмотр отчета
open htmlcov/index.html
```

### С маркерами
```bash
# Только быстрые тесты
pytest -m "not slow"

# Только критические тесты
pytest -m critical

# Только blockchain тесты
pytest -m blockchain
```

---

## 🎯 Best Practices

### 1. Написание тестов

#### ✅ Правильно
```python
def test_user_deposit_creates_transaction():
    """
    GIVEN: Пользователь с балансом 0
    WHEN: Создается депозит на $100
    THEN: 
        - Создается транзакция типа DEPOSIT
        - Баланс пользователя увеличивается на $100
        - ROI cap устанавливается корректно (500%)
    """
    # Arrange
    user = create_test_user(balance=Decimal("0"))
    deposit_amount = Decimal("100")
    
    # Act
    deposit = create_deposit(user, amount=deposit_amount, level=3)
    
    # Assert
    assert deposit.user_id == user.id
    assert deposit.amount == deposit_amount
    assert user.balance == deposit_amount
    assert deposit.roi_cap_amount == deposit_amount * 5
```

#### ❌ Неправильно
```python
def test_deposit():
    user = User()
    deposit = Deposit()
    assert deposit is not None
```

### 2. Именование тестов

**Формат:** `test_<component>_<action>_<expected_result>`

```python
# ✅ Хорошо
test_user_service_create_user_with_referrer_creates_referral_record()
test_withdrawal_service_request_below_minimum_raises_validation_error()
test_roi_calculation_at_500_percent_cap_stops_distribution()

# ❌ Плохо
test_user()
test_withdrawal()
test_roi()
```

### 3. Структура тестов (AAA Pattern)

```python
def test_referral_reward_calculation():
    # Arrange - Подготовка данных
    referrer = create_test_user()
    referred = create_test_user(referrer=referrer)
    deposit_amount = Decimal("100")
    
    # Act - Выполнение действия
    reward = calculate_referral_reward(
        referrer=referrer,
        referred=referred,
        deposit_amount=deposit_amount,
        level=1
    )
    
    # Assert - Проверка результата
    assert reward.amount == deposit_amount * Decimal("0.03")  # 3% для 1 уровня
    assert reward.referrer_id == referrer.id
    assert reward.referred_id == referred.id
```

### 4. Использование фикстур

```python
# conftest.py
@pytest.fixture
async def db_session():
    """Создает тестовую сессию БД"""
    async with async_session_maker() as session:
        yield session
        await session.rollback()

@pytest.fixture
def test_user():
    """Создает тестового пользователя"""
    return User(
        telegram_id=123456789,
        wallet_address="0x" + "1" * 40,
        financial_password=hash_password("test123")
    )

# test_file.py
async def test_deposit_service_create(db_session, test_user):
    service = DepositService(db_session)
    deposit = await service.create_deposit(test_user, amount=100, level=1)
    assert deposit.user_id == test_user.id
```

### 5. Моки и патчи

```python
from unittest.mock import Mock, patch, AsyncMock

async def test_withdrawal_with_blockchain_mock():
    # Mock blockchain service
    with patch('app.services.blockchain_service.BlockchainService') as mock_bc:
        mock_bc.return_value.send_payment = AsyncMock(
            return_value="0xabcd1234..."
        )
        
        service = WithdrawalService(db_session)
        tx_hash = await service.process_withdrawal(withdrawal_id=1)
        
        assert tx_hash.startswith("0x")
        mock_bc.return_value.send_payment.assert_called_once()
```

### 6. Параметризация тестов

```python
@pytest.mark.parametrize("level,amount,expected_roi_cap", [
    (1, Decimal("10"), Decimal("50")),
    (2, Decimal("50"), Decimal("250")),
    (3, Decimal("100"), Decimal("500")),
    (4, Decimal("150"), Decimal("750")),
    (5, Decimal("300"), Decimal("1500")),
])
async def test_deposit_roi_cap_calculation(level, amount, expected_roi_cap):
    """Проверка расчета ROI cap для всех уровней депозитов"""
    deposit = create_deposit(level=level, amount=amount)
    assert deposit.roi_cap_amount == expected_roi_cap
```

### 7. Маркеры

```python
@pytest.mark.slow
@pytest.mark.blockchain
async def test_deposit_monitoring_full_cycle():
    """Полный цикл мониторинга депозитов в блокчейне"""
    # Тест может занимать много времени
    pass

@pytest.mark.critical
async def test_user_balance_never_negative():
    """Критический тест: баланс никогда не может быть отрицательным"""
    pass
```

### 8. Проверка ошибок

```python
async def test_withdrawal_below_minimum_raises_error():
    """WHEN: Запрос вывода ниже минимума, THEN: Выбрасывается ошибка"""
    with pytest.raises(ValidationError) as exc_info:
        await withdrawal_service.create_withdrawal(
            user=test_user,
            amount=Decimal("5")  # Меньше минимума $10
        )
    
    assert "minimum withdrawal" in str(exc_info.value).lower()
```

### 9. Асинхронные тесты

```python
@pytest.mark.asyncio
async def test_concurrent_deposits():
    """Тест параллельного создания депозитов"""
    users = [create_test_user() for _ in range(10)]
    
    # Создаем депозиты параллельно
    deposits = await asyncio.gather(*[
        deposit_service.create_deposit(user, 100, 1)
        for user in users
    ])
    
    assert len(deposits) == 10
    assert all(d.status == "pending" for d in deposits)
```

### 10. Очистка после тестов

```python
@pytest.fixture
async def cleanup_test_data():
    """Очистка тестовых данных после теста"""
    yield
    # Cleanup code
    await db_session.execute(delete(User).where(User.telegram_id > 900000000))
    await db_session.commit()
```

---

## 📈 Метрики качества

### Целевые показатели

- ✅ **Покрытие кода:** ≥ 95%
- ✅ **Успешность тестов:** 100%
- ✅ **Время выполнения:** < 5 минут для всех тестов
- ✅ **Покрытие критических сценариев:** 100%

### Мониторинг

```bash
# Проверка покрытия
pytest --cov=app --cov=bot --cov-report=term-missing

# Отчет в HTML
pytest --cov=app --cov=bot --cov-report=html

# Отчет в XML (для CI/CD)
pytest --cov=app --cov=bot --cov-report=xml
```

---

## 🔄 CI/CD Integration

### GitHub Actions пример

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests
        run: |
          pytest --cov=app --cov=bot --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 📚 Дополнительные ресурсы

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Async Testing](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Версия:** 1.0.0  
**Дата создания:** 2025-11-16  
**Автор:** Claude AI  
**Статус:** ✅ Production Ready
