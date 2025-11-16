# 🧪 Сценарии применения тестов SigmaTrade Bot

## 📋 Содержание

- [Введение](#введение)
- [Типы тестов и сценарии применения](#типы-тестов-и-сценарии-применения)
- [Когда запускать какие тесты](#когда-запускать-какие-тесты)
- [Нагрузочные тесты](#нагрузочные-тесты)
- [CI/CD Pipelines](#cicd-pipelines)
- [Производственный мониторинг](#производственный-мониторинг)
- [Best Practices](#best-practices)

---

## 🎯 Введение

Этот документ описывает **когда**, **как** и **зачем** запускать различные типы тестов в проекте SigmaTrade Bot. Правильное применение тестов критично для поддержания качества кода и стабильности системы.

---

## 📊 Типы тестов и сценарии применения

### 1. Unit Tests (Модульные тесты)

**Когда запускать:**
- ✅ При каждом изменении кода
- ✅ Перед коммитом
- ✅ В CI/CD pipeline (обязательно)
- ✅ При локальной разработке (постоянно)

**Как запускать:**
```bash
# Все unit тесты
pytest tests/unit/ -v

# Только модели
pytest tests/unit/models/ -v

# Только сервисы
pytest tests/unit/services/ -v

# С покрытием
pytest tests/unit/ --cov=app --cov-report=html
```

**Сценарии использования:**

#### Сценарий 1: Разработка новой модели
```bash
# 1. Создаешь модель app/models/new_model.py
# 2. Пишешь тесты tests/unit/models/test_new_model.py
# 3. Запускаешь тесты
pytest tests/unit/models/test_new_model.py -v

# 4. Проверяешь покрытие
pytest tests/unit/models/test_new_model.py --cov=app.models.new_model --cov-report=term-missing
```

#### Сценарий 2: Исправление бага в сервисе
```bash
# 1. Воспроизводишь баг в тесте
pytest tests/unit/services/test_deposit_service.py::test_specific_bug -v

# 2. Исправляешь код
# 3. Проверяешь, что тест проходит
pytest tests/unit/services/test_deposit_service.py::test_specific_bug -v

# 4. Запускаешь все тесты сервиса
pytest tests/unit/services/test_deposit_service.py -v
```

#### Сценарий 3: Рефакторинг
```bash
# 1. Запускаешь все тесты до рефакторинга
pytest tests/unit/ -v > before.txt

# 2. Делаешь рефакторинг
# 3. Запускаешь тесты после
pytest tests/unit/ -v > after.txt

# 4. Сравниваешь результаты
diff before.txt after.txt
```

---

### 2. Integration Tests (Интеграционные тесты)

**Когда запускать:**
- ✅ После изменения нескольких связанных компонентов
- ✅ Перед merge в main ветку
- ✅ В CI/CD pipeline (обязательно)
- ✅ Раз в день (scheduled tests)

**Как запускать:**
```bash
# Все интеграционные тесты
pytest tests/integration/ -v

# Только workflow тесты
pytest tests/integration/workflows/ -v

# С детальным логированием
pytest tests/integration/ -v --log-cli-level=DEBUG
```

**Сценарии использования:**

#### Сценарий 1: Интеграция новой функции
```bash
# 1. Создал новый сервис и репозиторий
# 2. Написал integration тест
pytest tests/integration/workflows/test_new_feature_workflow.py -v

# 3. Проверил взаимодействие с БД
pytest tests/integration/workflows/ -v --tb=short
```

#### Сценарий 2: Проверка бизнес-процесса
```bash
# Тестируем полный flow депозита
pytest tests/integration/workflows/test_deposit_workflow.py -v

# Тестируем flow вывода
pytest tests/integration/workflows/test_withdrawal_workflow.py -v

# Тестируем реферальную систему
pytest tests/integration/workflows/test_referral_workflow.py -v
```

#### Сценарий 3: Тестирование после миграции БД
```bash
# 1. Применяешь миграцию
alembic upgrade head

# 2. Запускаешь интеграционные тесты
pytest tests/integration/ -v

# 3. Проверяешь, что ничего не сломалось
pytest tests/integration/test_database_integration.py -v
```

---

### 3. E2E Tests (Сквозные тесты)

**Когда запускать:**
- ✅ Перед релизом
- ✅ После major изменений
- ✅ В staging environment
- ✅ Раз в неделю (полный набор)

**Как запускать:**
```bash
# Все E2E тесты
pytest tests/e2e/ -v --tb=short

# По ролям
pytest tests/e2e/user_scenarios/ -v
pytest tests/e2e/admin_scenarios/ -v
pytest tests/e2e/system_scenarios/ -v

# Только критические сценарии
pytest tests/e2e/ -v -m critical
```

**Сценарии использования:**

#### Сценарий 1: Pre-release проверка
```bash
# 1. Запускаем все E2E тесты
pytest tests/e2e/ -v --html=report.html --self-contained-html

# 2. Проверяем критические пути
pytest tests/e2e/ -v -m critical

# 3. Проверяем user scenarios
pytest tests/e2e/user_scenarios/ -v
```

#### Сценарий 2: Регресс-тестирование после hotfix
```bash
# 1. Применил hotfix в депозитах
# 2. Запускаю связанные E2E тесты
pytest tests/e2e/user_scenarios/test_deposit_flow.py -v

# 3. Запускаю все зависимые тесты
pytest tests/e2e/ -v -k "deposit or balance"
```

#### Сценарий 3: Smoke tests в production
```bash
# Быстрая проверка основных функций
pytest tests/e2e/user_scenarios/ -v -m "not slow" --maxfail=1
```

---

### 4. Load Tests (Нагрузочные тесты)

**Когда запускать:**
- ✅ Перед релизом в production
- ✅ После оптимизации производительности
- ✅ При масштабировании системы
- ✅ Раз в месяц (плановые проверки)

**Как запускать:**
```bash
# Все нагрузочные тесты
pytest tests/load/ -v -m load

# Только быстрые тесты
pytest tests/load/ -v -m "load and not slow"

# Полный набор (включая sustained load)
pytest tests/load/ -v -m load --durations=10
```

**Сценарии использования:**

#### Сценарий 1: Baseline Performance Testing
```bash
# 1. Замеряем текущую производительность
pytest tests/load/test_load_database.py -v > baseline_db.txt
pytest tests/load/test_load_services.py -v > baseline_services.txt

# 2. Сохраняем результаты для сравнения
cat baseline_*.txt > baseline_report.txt
```

#### Сценарий 2: После оптимизации кода
```bash
# 1. Запускаем тесты до оптимизации
pytest tests/load/ -v --durations=10 > before_optimization.txt

# 2. Делаем оптимизацию (например, добавляем индексы)
# 3. Запускаем тесты после
pytest tests/load/ -v --durations=10 > after_optimization.txt

# 4. Сравниваем результаты
diff before_optimization.txt after_optimization.txt
```

#### Сценарий 3: Stress Testing перед большой нагрузкой
```bash
# 1. Проверяем устойчивость БД
pytest tests/load/test_load_database.py::test_database_connection_pool_stress -v

# 2. Проверяем устойчивость сервисов
pytest tests/load/test_load_services.py::test_mixed_workload_simulation -v

# 3. Длительный stress test
pytest tests/load/ -v -m slow --durations=0
```

#### Сценарий 4: Capacity Planning
```bash
# Определяем максимальную нагрузку
pytest tests/load/test_load_database.py::test_concurrent_user_creation -v
pytest tests/load/test_load_database.py::test_concurrent_deposits -v
pytest tests/load/test_load_services.py::test_concurrent_deposit_processing -v

# Анализируем результаты для планирования ресурсов
```

#### Сценарий 5: Continuous Load Testing
```bash
# Автоматический запуск нагрузочных тестов каждую ночь
# В cron:
# 0 2 * * * cd /path/to/project && pytest tests/load/ -v > /var/log/load_tests_$(date +\%Y\%m\%d).log 2>&1
```

---

### 5. Security Tests (Тесты безопасности)

**Когда запускать:**
- ✅ Перед каждым релизом
- ✅ После изменений в аутентификации/авторизации
- ✅ Раз в неделю (плановые проверки)
- ✅ При обнаружении уязвимостей

**Как запускать:**
```bash
# Все security тесты
pytest tests/security/ -v -m security

# Только authentication
pytest tests/security/test_authentication.py -v

# Только authorization
pytest tests/security/test_authorization.py -v

# SQL injection tests
pytest tests/security/test_sql_injection.py -v
```

**Сценарии использования:**

#### Сценарий 1: Аудит безопасности
```bash
# Полная проверка безопасности
pytest tests/security/ -v --html=security_report.html

# Проверка critical security issues
pytest tests/security/ -v -m "security and critical"
```

#### Сценарий 2: После изменений в авторизации
```bash
# Проверяем auth
pytest tests/security/test_authentication.py -v
pytest tests/security/test_authorization.py -v

# Проверяем rate limiting
pytest tests/security/test_rate_limiting.py -v
```

---

### 6. Blockchain Tests (Blockchain тесты)

**Когда запускать:**
- ✅ После изменений в blockchain интеграции
- ✅ Перед релизом
- ✅ При обновлении контрактов
- ✅ Раз в день (scheduled tests)

**Как запускать:**
```bash
# Все blockchain тесты
pytest tests/blockchain/ -v -m blockchain

# Только deposit monitoring
pytest tests/blockchain/test_deposit_monitoring.py -v

# С real blockchain (testnet)
pytest tests/blockchain/ -v --use-testnet
```

**Сценарии использования:**

#### Сценарий 1: Тестирование на testnet
```bash
# 1. Настраиваем testnet
export USE_TESTNET=true

# 2. Запускаем blockchain тесты
pytest tests/blockchain/ -v

# 3. Проверяем мониторинг депозитов
pytest tests/blockchain/test_deposit_monitoring.py -v
```

#### Сценарий 2: Проверка смарт-контракта
```bash
# Тестируем взаимодействие с контрактом
pytest tests/blockchain/test_smart_contract_interaction.py -v
```

---

## ⏰ Когда запускать какие тесты

### Локальная разработка (Continuous)
```bash
# При каждом изменении файла (watch mode)
pytest-watch tests/unit/

# Или используем nodemon
nodemon --exec pytest tests/unit/ --watch app/
```

### Перед коммитом (Pre-commit)
```bash
# Git hook в .git/hooks/pre-commit
#!/bin/bash
pytest tests/unit/ -v --maxfail=1
if [ $? -ne 0 ]; then
    echo "Unit tests failed. Commit aborted."
    exit 1
fi
```

### При создании Pull Request
```bash
# Запускаются автоматически в CI/CD
pytest tests/unit/ tests/integration/ -v --cov=app --cov-report=xml
```

### Перед merge в main
```bash
# Полный набор тестов (без slow)
pytest tests/ -v -m "not slow" --maxfail=5
```

### Перед релизом (Release Candidate)
```bash
# Абсолютно все тесты
pytest tests/ -v --html=full_test_report.html --self-contained-html
```

### Production Deployment
```bash
# Только критические тесты
pytest tests/e2e/ -v -m critical

# Smoke tests
pytest tests/e2e/user_scenarios/ -v -m "not slow" --maxfail=1
```

### Ночные тесты (Nightly)
```bash
# Полный набор включая slow тесты
pytest tests/ -v --html=nightly_report_$(date +\%Y\%m\%d).html
```

### Еженедельные тесты (Weekly)
```bash
# Нагрузочные тесты + security
pytest tests/load/ tests/security/ -v --html=weekly_report_$(date +\%Y\%m\%d).html
```

---

## 🚀 CI/CD Pipelines

### Pipeline 1: Fast Feedback (На каждый commit)
```yaml
name: Fast Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run unit tests
        run: pytest tests/unit/ -v --maxfail=5
```

### Pipeline 2: Pull Request Validation
```yaml
name: PR Tests
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pytest tests/unit/ -v
          pytest tests/integration/ -v
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### Pipeline 3: Pre-Release (На merge в main)
```yaml
name: Pre-Release Tests
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run all tests
        run: pytest tests/ -v -m "not slow"
      - name: Run E2E tests
        run: pytest tests/e2e/ -v -m critical
```

### Pipeline 4: Nightly Tests
```yaml
name: Nightly Tests
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run full test suite
        run: pytest tests/ -v --html=report.html
      - name: Upload report
        uses: actions/upload-artifact@v2
        with:
          name: test-report
          path: report.html
```

### Pipeline 5: Load Tests (Weekly)
```yaml
name: Weekly Load Tests
on:
  schedule:
    - cron: '0 3 * * 0'  # Sunday 3 AM
jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run load tests
        run: pytest tests/load/ -v --html=load_report.html
      - name: Compare with baseline
        run: ./scripts/compare_performance.sh
```

---

## 📊 Производственный мониторинг

### Health Check Tests
```bash
# Запускать каждые 5 минут
pytest tests/e2e/user_scenarios/test_basic_health.py -v --maxfail=1
```

### Smoke Tests после деплоя
```bash
#!/bin/bash
# post-deploy.sh

# Ждем 30 секунд после деплоя
sleep 30

# Запускаем smoke tests
pytest tests/e2e/ -v -m "smoke" --maxfail=1

if [ $? -ne 0 ]; then
    echo "Smoke tests failed! Rolling back..."
    ./rollback.sh
    exit 1
fi

echo "Smoke tests passed! Deployment successful."
```

### Performance Monitoring
```bash
# Запускать раз в час
pytest tests/load/test_load_database.py::test_database_connection_pool_stress -v

# Логировать результаты для трендов
pytest tests/load/ -v --json=performance_$(date +\%Y\%m\%d_\%H\%M).json
```

---

## 💡 Best Practices

### 1. Test Prioritization
```
P0 (Critical) → Запускать всегда
P1 (High) → Запускать в CI/CD
P2 (Medium) → Запускать перед релизом
P3 (Low) → Запускать в nightly
```

### 2. Test Selection Strategy
```bash
# Изменили модель User?
pytest tests/unit/models/test_user.py tests/integration/ -v -k "user"

# Изменили депозиты?
pytest tests/ -v -k "deposit"

# Изменили авторизацию?
pytest tests/security/ tests/unit/services/test_user_service.py -v
```

### 3. Fail Fast Strategy
```bash
# Останавливаемся на первой ошибке
pytest tests/ -v --maxfail=1 -x

# Или на 5 ошибках
pytest tests/ -v --maxfail=5
```

### 4. Parallel Execution
```bash
# Запуск тестов параллельно
pytest tests/unit/ -v -n auto  # auto detect CPU cores
pytest tests/unit/ -v -n 4     # use 4 workers
```

### 5. Test Coverage Goals
```
Unit Tests: ≥ 90% coverage
Integration Tests: ≥ 80% coverage
E2E Tests: 100% critical paths
Load Tests: All performance-critical operations
```

### 6. Test Documentation
```python
def test_user_deposit_with_referrer():
    """
    Test deposit creation with referral rewards.
    
    GIVEN: User with active referrer
    WHEN: User creates deposit
    THEN:
        - Deposit created successfully
        - Referrer receives 3% commission
        - Balance updated correctly
        - Transaction recorded
    
    Related: Issue #123, Feature #456
    Priority: P0 (Critical)
    """
```

---

## 📚 Дополнительные ресурсы

- [TESTING_SYSTEM_DOCUMENTATION.md](./TESTING_SYSTEM_DOCUMENTATION.md) - Полная документация
- [TEST_COVERAGE_MAP.md](./TEST_COVERAGE_MAP.md) - Карта покрытия
- [README.md](./README.md) - Быстрый старт

---

## 🎯 Итоговые рекомендации

### Ежедневно
```bash
pytest tests/unit/ -v
```

### Перед коммитом
```bash
pytest tests/unit/ -v --maxfail=1
```

### Перед релизом
```bash
pytest tests/ -v --html=release_report.html
```

### Production
```bash
pytest tests/e2e/ -v -m critical --maxfail=1
```

---

**Версия:** 1.0.0  
**Дата:** 2025-11-16  
**Статус:** ✅ Production Ready
