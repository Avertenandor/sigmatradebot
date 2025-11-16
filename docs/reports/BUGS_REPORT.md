# 🐛 ОТЧЕТ О НАЙДЕННЫХ БАГАХ
**Дата:** 16 ноября 2025  
**Анализатор:** Claude  
**Статус:** Требуется немедленное исправление

---

## 🔴 КРИТИЧНЫЕ ПРОБЛЕМЫ (P0) - БЛОКИРУЮЩИЕ

### 1. **КОДИРОВКА ФАЙЛОВ - UTF-16 ВМЕСТО UTF-8**
**Файлы:**
- `app/services/blockchain/blockchain_service.py`
- `app/services/blockchain/deposit_processor.py`
- `app/services/blockchain/payment_sender.py`
- `app/services/blockchain/event_monitor.py`

**Проблема:** Все файлы в директории `blockchain/` имеют кодировку UTF-16 вместо UTF-8. Каждый символ занимает 2 байта.

**Последствия:**
- Невозможность нормальной работы с файлами
- Проблемы с импортами
- Модули закомментированы в main.py из-за этой проблемы

**Приоритет:** 🔴 **P0 - КРИТИЧНО**

**Решение:**
```bash
# Конвертация файлов в UTF-8
iconv -f UTF-16 -t UTF-8 app/services/blockchain/blockchain_service.py > temp && mv temp app/services/blockchain/blockchain_service.py
iconv -f UTF-16 -t UTF-8 app/services/blockchain/deposit_processor.py > temp && mv temp app/services/blockchain/deposit_processor.py
iconv -f UTF-16 -t UTF-8 app/services/blockchain/payment_sender.py > temp && mv temp app/services/blockchain/payment_sender.py
iconv -f UTF-16 -t UTF-8 app/services/blockchain/event_monitor.py > temp && mv temp app/services/blockchain/event_monitor.py
```

---

### 2. **ОТСУТСТВУЕТ ERROR HANDLER В BOT**
**Файл:** `bot/main.py`

**Проблема:** Нет глобального error handler для необработанных исключений в боте.

**Последствия:**
- При необработанном исключении бот упадет
- Нет логирования критичных ошибок
- Пользователи получат "500 Internal Error" без объяснений

**Приоритет:** 🔴 **P0 - КРИТИЧНО**

**Решение:**
```python
# Добавить в bot/main.py перед dp.start_polling

@dp.error()
async def error_handler(event, exc):
    """Global error handler."""
    logger.exception(f"Critical error: {exc}")
    
    if event.update.message:
        try:
            await event.update.message.answer(
                "⚠️ Произошла ошибка. Попробуйте позже или обратитесь в поддержку."
            )
        except Exception:
            pass
    
    return True  # Mark as handled
```

---

### 3. **УСТАРЕВШЕЕ ИСПОЛЬЗОВАНИЕ datetime.utcnow()**
**Файлы:**
- `app/models/user.py`
- `app/models/deposit.py`
- `app/models/transaction.py`
- Все модели с timestamp полями

**Проблема:** `datetime.utcnow()` устарело в Python 3.12+

**Последствия:**
- Warnings при запуске
- Потенциальные проблемы с часовыми поясами
- Deprecated функционал

**Приоритет:** 🔴 **P0 - КРИТИЧНО**

**Решение:**
```python
# БЫЛО:
created_at: Mapped[datetime] = mapped_column(
    DateTime, default=datetime.utcnow, nullable=False
)

# СТАЛО:
from datetime import datetime, timezone

created_at: Mapped[datetime] = mapped_column(
    DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
)
```

---

## 🟡 ВЫСОКИЙ ПРИОРИТЕТ (P1) - КРИТИЧНЫЕ БАГИ

### 4. **ОТСУТСТВУЮТ CONSTRAINTS В МОДЕЛЯХ**
**Файлы:** Все модели

**Проблема:** Нет CHECK constraints для критичных полей

**Примеры:**
```python
# User.balance может быть отрицательным
# Deposit.level может быть 0 или > 5
# Transaction.amount может быть отрицательным
```

**Последствия:**
- Некорректные данные в БД
- Отрицательные балансы
- Невалидные уровни депозитов

**Приоритет:** 🟡 **P1 - ВЫСОКИЙ**

**Решение:**
```python
# app/models/user.py
from sqlalchemy import CheckConstraint

__table_args__ = (
    CheckConstraint('balance >= 0', name='check_balance_non_negative'),
    CheckConstraint('total_earned >= 0', name='check_total_earned_non_negative'),
    CheckConstraint('pending_earnings >= 0', name='check_pending_earnings_non_negative'),
)

# app/models/deposit.py
__table_args__ = (
    CheckConstraint('level >= 1 AND level <= 5', name='check_level_range'),
    CheckConstraint('amount > 0', name='check_amount_positive'),
    CheckConstraint('roi_cap_amount >= 0', name='check_roi_cap_non_negative'),
    CheckConstraint('roi_paid_amount >= 0', name='check_roi_paid_non_negative'),
    CheckConstraint('roi_paid_amount <= roi_cap_amount', name='check_roi_paid_not_exceeds_cap'),
)

# app/models/transaction.py
__table_args__ = (
    CheckConstraint('amount > 0', name='check_amount_positive'),
    CheckConstraint('balance_before >= 0', name='check_balance_before_non_negative'),
    CheckConstraint('balance_after >= 0', name='check_balance_after_non_negative'),
)
```

---

### 5. **НЕТ ВАЛИДАЦИИ В settings.py**
**Файл:** `app/config/settings.py`

**Проблема:** Отсутствует валидация критичных настроек

**Примеры:**
- `deposit_level_*` может быть отрицательным
- `roi_daily_percent` может быть > 100%
- `wallet_address` не проверяется на валидность
- `get_admin_ids()` может упасть на невалидных данных

**Последствия:**
- Некорректная конфигурация
- Краш при старте
- Невалидные admin IDs

**Приоритет:** 🟡 **P1 - ВЫСОКИЙ**

**Решение:**
```python
from pydantic import field_validator, Field

class Settings(BaseSettings):
    # ... existing fields ...
    
    deposit_level_1: float = Field(default=50.0, gt=0)
    deposit_level_2: float = Field(default=100.0, gt=0)
    deposit_level_3: float = Field(default=250.0, gt=0)
    deposit_level_4: float = Field(default=500.0, gt=0)
    deposit_level_5: float = Field(default=1000.0, gt=0)
    
    roi_daily_percent: float = Field(default=0.02, gt=0, le=1.0)
    roi_cap_multiplier: float = Field(default=5.0, gt=0, le=10.0)
    
    @field_validator('wallet_address', 'system_wallet_address')
    @classmethod
    def validate_wallet_address(cls, v: str) -> str:
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError(f'Invalid wallet address: {v}')
        try:
            int(v[2:], 16)
        except ValueError:
            raise ValueError(f'Invalid wallet address format: {v}')
        return v.lower()
    
    def get_admin_ids(self) -> list[int]:
        """Parse admin IDs from comma-separated string."""
        if not self.admin_telegram_ids:
            return []
        
        result = []
        for id_ in self.admin_telegram_ids.split(","):
            id_stripped = id_.strip()
            if not id_stripped:
                continue
            try:
                result.append(int(id_stripped))
            except ValueError:
                logger.warning(f"Invalid admin ID: {id_stripped}")
                continue
        return result
```

---

### 6. **НЕТ ОБРАБОТКИ ТРАНЗАКЦИЙ В deposit_service.py**
**Файл:** `app/services/deposit_service.py`

**Проблема:** Нет rollback при ошибках commit()

**Последствия:**
- Потеря данных при ошибке
- Несогласованность БД
- Partial updates

**Приоритет:** 🟡 **P1 - ВЫСОКИЙ**

**Решение:**
```python
async def create_deposit(
    self,
    user_id: int,
    level: int,
    amount: Decimal,
    tx_hash: Optional[str] = None,
) -> Deposit:
    """Create new deposit with proper error handling."""
    # Validate level
    if not 1 <= level <= 5:
        raise ValueError("Level must be 1-5")
    
    # Validate amount
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    try:
        # Calculate ROI cap from settings
        from app.config.settings import settings
        roi_multiplier = Decimal(str(settings.roi_cap_multiplier))
        roi_cap = amount * roi_multiplier
        
        deposit = await self.deposit_repo.create(
            user_id=user_id,
            level=level,
            amount=amount,
            tx_hash=tx_hash,
            roi_cap_amount=roi_cap,
            status=TransactionStatus.PENDING.value,
        )
        
        await self.session.commit()
        logger.info(f"Deposit created", extra={"deposit_id": deposit.id})
        
        return deposit
        
    except Exception as e:
        await self.session.rollback()
        logger.error(f"Failed to create deposit: {e}")
        raise
```

---

### 7. **WITHDRAWAL НЕ ОБНОВЛЯЕТ БАЛАНС**
**Файл:** `app/services/withdrawal_service.py`

**Проблема:** 
1. При создании withdrawal баланс не уменьшается
2. При отмене withdrawal баланс не возвращается
3. При reject баланс не возвращается

**Последствия:**
- Баланс пользователя замораживается навсегда
- Невозможность использовать средства
- Loss of funds

**Приоритет:** 🟡 **P1 - ВЫСОКИЙ**

**Решение:**
```python
async def request_withdrawal(
    self,
    user_id: int,
    amount: Decimal,
    available_balance: Decimal,
) -> tuple[Optional[Transaction], Optional[str]]:
    """Request withdrawal with balance deduction."""
    # ... existing validation ...
    
    try:
        # Deduct balance BEFORE creating transaction
        user.balance = user.balance - amount
        
        # Create withdrawal transaction
        transaction = await self.transaction_repo.create(
            user_id=user_id,
            type=TransactionType.WITHDRAWAL.value,
            amount=amount,
            balance_before=available_balance,
            balance_after=user.balance,
            to_address=user.wallet_address,
            status=TransactionStatus.PENDING.value,
        )
        
        await self.session.commit()
        
        return transaction, None
        
    except Exception as e:
        await self.session.rollback()
        logger.error(f"Failed to create withdrawal: {e}")
        return None, "Ошибка создания заявки на вывод"

async def cancel_withdrawal(
    self, transaction_id: int, user_id: int
) -> tuple[bool, Optional[str]]:
    """Cancel withdrawal and RETURN BALANCE."""
    # ... existing code to find transaction ...
    
    try:
        # Get user and return balance
        stmt_user = select(User).where(User.id == user_id).with_for_update()
        result_user = await self.session.execute(stmt_user)
        user = result_user.scalar_one_or_none()
        
        if user:
            user.balance = user.balance + transaction.amount
        
        transaction.status = TransactionStatus.FAILED.value
        await self.session.commit()
        
        return True, None
        
    except Exception as e:
        await self.session.rollback()
        logger.error(f"Failed to cancel withdrawal: {e}")
        return False, "Ошибка отмены заявки"

# То же самое для reject_withdrawal
```

---

## 🟢 СРЕДНИЙ ПРИОРИТЕТ (P2) - ВАЖНЫЕ УЛУЧШЕНИЯ

### 8. **НЕТ ИНДЕКСОВ НА ВАЖНЫХ ПОЛЯХ**
**Файлы:** Модели

**Проблема:** Отсутствуют индексы для часто используемых полей

**Примеры:**
- `User.email` - поиск по email
- `User.phone` - поиск по телефону
- `Transaction.created_at` - сортировка по дате
- `Deposit.confirmed_at` - фильтрация подтвержденных

**Последствия:**
- Медленные запросы
- Full table scan
- Проблемы с производительностью при росте данных

**Приоритет:** 🟢 **P2 - СРЕДНИЙ**

**Решение:**
```python
# app/models/user.py
email: Mapped[Optional[str]] = mapped_column(
    String(255), nullable=True, index=True
)
phone: Mapped[Optional[str]] = mapped_column(
    String(50), nullable=True, index=True
)

# app/models/transaction.py  
created_at: Mapped[datetime] = mapped_column(
    DateTime, default=lambda: datetime.now(timezone.utc), 
    nullable=False, index=True
)

# app/models/deposit.py
confirmed_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime, nullable=True, index=True
)
```

---

### 9. **ИМПОРТЫ ВНУТРИ ФУНКЦИЙ**
**Файл:** `app/services/user_service.py`

**Проблема:** Импорты делаются внутри функций вместо начала файла

```python
async def get_user_balance(self, user_id: int) -> dict:
    from app.repositories.deposit_repository import DepositRepository  # ❌ Плохо
    from app.repositories.transaction_repository import TransactionRepository
    from app.models.enums import TransactionType, TransactionStatus
```

**Последствия:**
- Медленнее выполнение
- Плохая читаемость кода
- Circular import проблемы

**Приоритет:** 🟢 **P2 - СРЕДНИЙ**

**Решение:**
```python
# Переместить в начало файла
from app.repositories.deposit_repository import DepositRepository
from app.repositories.transaction_repository import TransactionRepository
from app.models.enums import TransactionType, TransactionStatus
```

---

### 10. **НЕТ GRACEFUL SHUTDOWN**
**Файл:** `bot/main.py`

**Проблема:** Бот не обрабатывает сигналы остановки корректно

**Последствия:**
- Незакрытые соединения с БД
- Redis connections leak
- Blockchain connections не закрываются

**Приоритет:** 🟢 **P2 - СРЕДНИЙ**

**Решение:**
```python
import signal

async def shutdown(signal, dp, redis_client):
    """Graceful shutdown."""
    logger.info(f"Received exit signal {signal.name}")
    
    # Stop polling
    await dp.stop_polling()
    
    # Close Redis
    if redis_client:
        await redis_client.aclose()
    
    # Close bot session
    await bot.session.close()
    
    # Close DB connections
    await async_session_maker.close_all()
    
    logger.info("Shutdown complete")

async def main():
    # ... existing initialization ...
    
    # Setup signal handlers
    loop = asyncio.get_running_loop()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(shutdown(s, dp, redis_client))
        )
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.exception(f"Polling error: {e}")
    finally:
        await shutdown(None, dp, redis_client)
```

---

## 📊 СТАТИСТИКА НАЙДЕННЫХ ПРОБЛЕМ

| Приоритет | Количество | Статус |
|-----------|-----------|---------|
| 🔴 P0 (Критичные) | 3 | Требуют немедленного исправления |
| 🟡 P1 (Высокие) | 4 | Требуют исправления в течение 1-2 дней |
| 🟢 P2 (Средние) | 3 | Требуют исправления в течение недели |
| **ИТОГО** | **10** | - |

---

## 🎯 ПЛАН ИСПРАВЛЕНИЯ

### Этап 1: Критичные проблемы (СЕГОДНЯ)
1. ✅ Конвертировать файлы blockchain в UTF-8
2. ✅ Добавить error handler в bot
3. ✅ Исправить datetime.utcnow() во всех моделях

**Время:** 2-3 часа  
**Ответственный:** Разработчик

---

### Этап 2: Высокий приоритет (1-2 ДНЯ)
1. ✅ Добавить constraints в модели
2. ✅ Добавить валидацию в settings
3. ✅ Исправить обработку транзакций в deposit_service
4. ✅ Исправить баланс в withdrawal_service

**Время:** 4-6 часов  
**Ответственный:** Разработчик

---

### Этап 3: Средний приоритет (НЕДЕЛЯ)
1. ✅ Добавить индексы в модели
2. ✅ Убрать импорты из функций
3. ✅ Добавить graceful shutdown

**Время:** 2-3 часа  
**Ответственный:** Разработчик

---

## 🔧 РЕКОМЕНДАЦИИ

1. **Запустить линтер:** `pylint app/ bot/`
2. **Запустить type checker:** `mypy app/ bot/`
3. **Запустить тесты:** `pytest tests/`
4. **Проверить миграции:** `alembic check`
5. **Создать новые миграции:** `alembic revision --autogenerate -m "Add constraints and indexes"`

---

## 📝 NOTES

- Все критичные проблемы влияют на работоспособность бота
- Рекомендуется исправить P0 перед деплоем на production
- P1 проблемы могут привести к потере данных пользователей
- P2 проблемы влияют на производительность и качество кода

---

**Конец отчета**  
**Дата создания:** 16 ноября 2025  
**Анализ выполнен:** Claude AI
