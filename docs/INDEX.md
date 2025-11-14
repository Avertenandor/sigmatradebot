# 📚 Документация SigmaTrade Bot

## 📂 Структура документации

### 🐍 Миграция на Python (ROOT)
- [PYTHON_MIGRATION_README.md](../PYTHON_MIGRATION_README.md) - 🔴 **ГЛАВНЫЙ ДОКУМЕНТ** - Навигация по миграции
- [START_HERE_CLAUDE.md](../START_HERE_CLAUDE.md) - 🚀 Быстрый старт для Claude
- [MIGRATION_SUMMARY.md](../MIGRATION_SUMMARY.md) - Краткое резюме миграции
- [CLOUD_CODE_PYTHON_MIGRATION.md](../CLOUD_CODE_PYTHON_MIGRATION.md) - Часть 1: Модули 1-8
- [CLOUD_CODE_PYTHON_MIGRATION_PART2.md](../CLOUD_CODE_PYTHON_MIGRATION_PART2.md) - Часть 2: Модули 9-16
- [CLOUD_CODE_PYTHON_MIGRATION_PART3.md](../CLOUD_CODE_PYTHON_MIGRATION_PART3.md) - Часть 3: Модули 17-20
- [CLOUD_CODE_PYTHON_MIGRATION_PART4.md](../CLOUD_CODE_PYTHON_MIGRATION_PART4.md) - Часть 4: Модули 21-25
- [CLOUD_CODE_PYTHON_MIGRATION_PART5.md](../CLOUD_CODE_PYTHON_MIGRATION_PART5.md) - 🔴 **Часть 5: Критичные пропущенные компоненты** (Модули 26-35)
- [MIGRATION_GAP_ANALYSIS.md](../MIGRATION_GAP_ANALYSIS.md) - Анализ пропусков в миграции (55 пунктов)
- [MIGRATION_FIXES_REQUIRED.md](../MIGRATION_FIXES_REQUIRED.md) - Критичные проблемы для исправления

### 🧹 Подготовка сервера (ROOT)
- [SERVER_MIGRATION_GUIDE.md](../SERVER_MIGRATION_GUIDE.md) - 📖 **Полный гайд по миграции сервера**
- [CURRENT_SERVER_CONFIG.md](../CURRENT_SERVER_CONFIG.md) - Текущая конфигурация сервера (для справки)
- [cleanup_server.ps1](../cleanup_server.ps1) - PowerShell скрипт для запуска очистки (Windows)
- [server_cleanup.sh](../server_cleanup.sh) - Bash скрипт очистки сервера (выполняется на сервере)

### 🏗️ Архитектура (`architecture/`)
- [ARCHITECTURE.md](architecture/ARCHITECTURE.md) - Общая архитектура системы

### 🚀 Деплой и операции (`deployment/`)
- [DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md) - Руководство по деплою (TypeScript)
- [OPERATIONS.md](deployment/OPERATIONS.md) - Операционные процедуры
- [ROLLBACK_PROCEDURES.md](deployment/ROLLBACK_PROCEDURES.md) - Процедуры отката
- [SIGMATRADE_SERVER_SETUP.md](deployment/SIGMATRADE_SERVER_SETUP.md) - Настройка сервера

### 💻 Разработка (`development/`)
- [REFACTORING_MASTER_PLAN.md](development/REFACTORING_MASTER_PLAN.md) - Мастер-план рефакторинга
- [REFACTORING_PROGRESS.md](development/REFACTORING_PROGRESS.md) - Прогресс рефакторинга
- [IMPLEMENTATION_PLAN.md](development/IMPLEMENTATION_PLAN.md) - План реализации
- [P0_CRITICAL_FIXES.md](development/P0_CRITICAL_FIXES.md) - Критические исправления P0
- [QUICK_FIXES.md](development/QUICK_FIXES.md) - Быстрые исправления
- [FIX_ERRORS_TZ.md](development/FIX_ERRORS_TZ.md) - Инструкции для Claude Code

### 🧪 Тестирование (`testing/`)
- [TEST_COVERAGE_REPORT.md](testing/TEST_COVERAGE_REPORT.md) - Отчет о покрытии тестами
- [README.md](../tests/README.md) - Инструкции по тестированию (в папке tests/)

### 📖 Гайды и инструкции (`guides/`)
- [AUDIT_LOGGING_GUIDE.md](guides/AUDIT_LOGGING_GUIDE.md) - Гайд по аудит-логированию
- [MIGRATION_GUIDE.md](guides/MIGRATION_GUIDE.md) - Руководство по миграциям
- [MIGRATIONS.md](guides/MIGRATIONS.md) - Документация миграций БД
- [MONITORING.md](guides/MONITORING.md) - Мониторинг системы
- [POST_AUDIT_CHECKLIST.md](guides/POST_AUDIT_CHECKLIST.md) - Чеклист после аудита
- [PRODUCTION_READINESS.md](guides/PRODUCTION_READINESS.md) - Готовность к продакшену
- [TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md) - Решение проблем
- [ROI_SYSTEM_ADMIN_GUIDE.md](ROI_SYSTEM_ADMIN_GUIDE.md) - Гайд администратора ROI
- [ROI_SYSTEM_USER_GUIDE.md](ROI_SYSTEM_USER_GUIDE.md) - Гайд пользователя ROI

### 📊 Отчеты (`reports/`)
- [CHANGELOG.md](reports/CHANGELOG.md) - История изменений

---

## 🔍 Быстрый поиск

### Если вы хотите...

#### 🐍 Миграция на Python
- **🔴 Начать миграцию** → [PYTHON_MIGRATION_README.md](../PYTHON_MIGRATION_README.md)
- **🚀 Быстрый старт для Claude** → [START_HERE_CLAUDE.md](../START_HERE_CLAUDE.md)
- **📖 Подготовить сервер** → [SERVER_MIGRATION_GUIDE.md](../SERVER_MIGRATION_GUIDE.md)
- **🧹 Очистить сервер (PowerShell)** → [cleanup_server.ps1](../cleanup_server.ps1)
- **📋 Текущая конфигурация** → [CURRENT_SERVER_CONFIG.md](../CURRENT_SERVER_CONFIG.md)
- **🔍 Анализ пропусков** → [MIGRATION_GAP_ANALYSIS.md](../MIGRATION_GAP_ANALYSIS.md)
- **🔧 Критичные исправления** → [MIGRATION_FIXES_REQUIRED.md](../MIGRATION_FIXES_REQUIRED.md)

#### 🚀 TypeScript версия (текущая)
- **Развернуть бота** → [DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md)
- **Понять архитектуру** → [ARCHITECTURE.md](architecture/ARCHITECTURE.md)
- **Исправить ошибки** → [TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)
- **Запустить тесты** → [Тестирование](../tests/README.md)
- **Откатить изменения** → [ROLLBACK_PROCEDURES.md](deployment/ROLLBACK_PROCEDURES.md)
- **Настроить сервер** → [SIGMATRADE_SERVER_SETUP.md](deployment/SIGMATRADE_SERVER_SETUP.md)
- **Провести миграцию БД** → [MIGRATION_GUIDE.md](guides/MIGRATION_GUIDE.md)
- **Подготовить к продакшену** → [PRODUCTION_READINESS.md](guides/PRODUCTION_READINESS.md)

---

## 🎯 Приоритеты на 2025-11-14

### 🔴 Критично (сейчас)
1. **Миграция на Python 3.11** - Основная задача
2. **Подготовка сервера** - Запустить `cleanup_server.ps1`
3. **Проверка документации** - Убедиться что ничего не упущено

### ⚡ Следующие шаги (после миграции)
1. Развертывание Python версии на сервере
2. Тестирование всех функций
3. Мониторинг первых 24 часов
4. Удаление бэкапов TypeScript (через неделю)

---

**Последнее обновление:** 2025-11-14  
**Версия документации:** 2.0 (Python Migration)

