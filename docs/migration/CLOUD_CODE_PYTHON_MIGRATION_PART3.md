# 🐍 ТЕХНИЧЕСКОЕ ЗАДАНИЕ: Миграция на Python - ЧАСТЬ 3 (НЕДОСТАЮЩИЕ ДЕТАЛИ)

**Полная детализация ВСЕХ компонентов которые были упущены в частях 1-2**

---

## ⚠️ КРИТИЧНО: ЭТА ЧАСТЬ ОБЯЗАТЕЛЬНА!

В частях 1-2 я дал "скелет" проекта. Но для ПОЛНОЦЕННОГО бота нужно
реализовать ВСЕ детали описанные ниже. БЕЗ этих деталей бот НЕ БУДЕТ 
работать полноценно!

---

## 📱 МОДУЛЬ 10: Keyboards (ПОЛНАЯ РЕАЛИЗАЦИЯ)

### Структура keyboards/

```
app/bot/keyboards/
├── __init__.py
├── base.py              # Базовые builders
├── main.py              # Главное меню
├── profile.py           # Профиль
├── deposit.py           # Депозиты
├── withdrawal.py        # Выводы
├── referral.py          # Рефералы
├── admin.py             # Админка
├── support.py           # Поддержка
├── settings.py          # Настройки
└── pagination.py        # Пагинация
```

### Полный код ВСЕХ keyboards

**Файл: `app/bot/keyboards/base.py`**
```python
"""Base keyboard builders."""
from typing import List, Optional, Callable
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import (
    ReplyKeyboardBuilder,
    InlineKeyboardBuilder
)


def build_reply_keyboard(
    buttons: List[str],
    resize: bool = True,
    one_time: bool = False,
    row_width: int = 2
) -> ReplyKeyboardMarkup:
    """
    Построение reply клавиатуры.
    
    Args:
        buttons: Список текстов кнопок
        resize: Автоматический resize
        one_time: Скрыть после нажатия
        row_width: Кнопок в ряду
        
    Returns:
        Reply клавиатура
    """
    builder = ReplyKeyboardBuilder()
    
    for text in buttons:
        builder.add(KeyboardButton(text=text))
    
    builder.adjust(row_width)
    
    return builder.as_markup(
        resize_keyboard=resize,
        one_time_keyboard=one_time
    )


def build_inline_keyboard(
    buttons: List[tuple[str, str]],
    row_width: int = 2
) -> InlineKeyboardMarkup:
    """
    Построение inline клавиатуры.
    
    Args:
        buttons: Список (text, callback_data)
        row_width: Кнопок в ряду
        
    Returns:
        Inline клавиатура
    """
    builder = InlineKeyboardBuilder()
    
    for text, callback_data in buttons:
        builder.add(
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data
            )
        )
    
    builder.adjust(row_width)
    return builder.as_markup()


def add_back_button(
    builder: InlineKeyboardBuilder,
    callback_data: str = "back"
) -> InlineKeyboardBuilder:
    """
    Добавить кнопку "Назад".
    
    Args:
        builder: Builder клавиатуры
        callback_data: Callback для кнопки
        
    Returns:
        Builder с кнопкой назад
    """
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=callback_data
        )
    )
    return builder


def add_close_button(
    builder: InlineKeyboardBuilder
) -> InlineKeyboardBuilder:
    """
    Добавить кнопку "Закрыть".
    
    Args:
        builder: Builder клавиатуры
        
    Returns:
        Builder с кнопкой закрыть
    """
    builder.row(
        InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="close"
        )
    )
    return builder
```

**Файл: `app/bot/keyboards/main.py`**
```python
"""Main menu keyboard."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Главное меню.
    
    Args:
        is_admin: Админ ли пользователь
        
    Returns:
        Главная клавиатура
    """
    builder = ReplyKeyboardBuilder()
    
    # Основные кнопки
    builder.add(KeyboardButton(text="👤 Профиль"))
    builder.add(KeyboardButton(text="💰 Баланс"))
    
    builder.add(KeyboardButton(text="📥 Депозит"))
    builder.add(KeyboardButton(text="📤 Вывод"))
    
    builder.add(KeyboardButton(text="👥 Рефералы"))
    builder.add(KeyboardButton(text="📊 Статистика"))
    
    builder.add(KeyboardButton(text="💼 ROI"))
    builder.add(KeyboardButton(text="🎁 Бонусы"))
    
    builder.add(KeyboardButton(text="⚙️ Настройки"))
    builder.add(KeyboardButton(text="📞 Поддержка"))
    
    # Админ кнопка
    if is_admin:
        builder.add(KeyboardButton(text="🔧 Админ"))
    
    # 2 кнопки в ряду
    builder.adjust(2)
    
    return builder.as_markup(resize_keyboard=True)
```

**Файл: `app/bot/keyboards/deposit.py`**
```python
"""Deposit keyboards."""
from decimal import Decimal
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_deposit_menu() -> InlineKeyboardMarkup:
    """Меню депозита."""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="💵 Новый депозит",
        callback_data="deposit:new"
    ))
    builder.add(InlineKeyboardButton(
        text="📋 Мои депозиты",
        callback_data="deposit:list"
    ))
    builder.add(InlineKeyboardButton(
        text="❓ Как пополнить",
        callback_data="deposit:help"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_deposit_amount_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора суммы депозита."""
    builder = InlineKeyboardBuilder()
    
    amounts = [
        ("0.01 BNB", "deposit:amount:0.01"),
        ("0.05 BNB", "deposit:amount:0.05"),
        ("0.1 BNB", "deposit:amount:0.1"),
        ("0.5 BNB", "deposit:amount:0.5"),
        ("1 BNB", "deposit:amount:1"),
        ("5 BNB", "deposit:amount:5"),
        ("10 BNB", "deposit:amount:10"),
        ("💎 Своя сумма", "deposit:amount:custom"),
    ]
    
    for text, callback_data in amounts:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        ))
    
    builder.adjust(2)
    
    # Кнопка назад
    builder.row(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="deposit:menu"
    ))
    
    return builder.as_markup()


def get_deposit_confirm_keyboard(
    deposit_id: int
) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения депозита.
    
    Args:
        deposit_id: ID депозита
        
    Returns:
        Keyboard с кнопками подтверждения
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="✅ Я отправил средства",
        callback_data=f"deposit:confirm:{deposit_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="🔄 Проверить статус",
        callback_data=f"deposit:check:{deposit_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Отменить",
        callback_data=f"deposit:cancel:{deposit_id}"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_deposit_list_keyboard(
    deposits: list,
    page: int = 0,
    per_page: int = 5
) -> InlineKeyboardMarkup:
    """
    Клавиатура списка депозитов с пагинацией.
    
    Args:
        deposits: Список депозитов
        page: Номер страницы
        per_page: Депозитов на странице
        
    Returns:
        Keyboard со списком
    """
    builder = InlineKeyboardBuilder()
    
    start = page * per_page
    end = start + per_page
    page_deposits = deposits[start:end]
    
    for deposit in page_deposits:
        status_emoji = {
            "pending": "⏳",
            "confirming": "🔄",
            "confirmed": "✅",
            "failed": "❌"
        }.get(deposit.status, "❓")
        
        builder.add(InlineKeyboardButton(
            text=(
                f"{status_emoji} {deposit.amount} BNB - "
                f"{deposit.created_at.strftime('%d.%m.%Y')}"
            ),
            callback_data=f"deposit:view:{deposit.id}"
        ))
    
    builder.adjust(1)
    
    # Пагинация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"deposit:list:{page-1}"
        ))
    if end < len(deposits):
        nav_buttons.append(InlineKeyboardButton(
            text="Вперед ▶️",
            callback_data=f"deposit:list:{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Кнопка в меню
    builder.row(InlineKeyboardButton(
        text="🏠 Главное меню",
        callback_data="main_menu"
    ))
    
    return builder.as_markup()
```

**Файл: `app/bot/keyboards/withdrawal.py`**
```python
"""Withdrawal keyboards."""
from decimal import Decimal
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_withdrawal_menu() -> InlineKeyboardMarkup:
    """Меню вывода средств."""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="💸 Новый вывод",
        callback_data="withdrawal:new"
    ))
    builder.add(InlineKeyboardButton(
        text="📋 Мои выводы",
        callback_data="withdrawal:list"
    ))
    builder.add(InlineKeyboardButton(
        text="❓ Условия вывода",
        callback_data="withdrawal:help"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_withdrawal_amount_keyboard(
    balance: Decimal
) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора суммы вывода.
    
    Args:
        balance: Текущий баланс пользователя
        
    Returns:
        Keyboard с вариантами сумм
    """
    builder = InlineKeyboardBuilder()
    
    # Проценты от баланса
    percents = [25, 50, 75, 100]
    
    for percent in percents:
        amount = balance * Decimal(percent) / Decimal(100)
        if amount > 0:
            builder.add(InlineKeyboardButton(
                text=f"{percent}% ({amount:.4f} BNB)",
                callback_data=f"withdrawal:amount:{amount}"
            ))
    
    # Своя сумма
    builder.add(InlineKeyboardButton(
        text="💎 Своя сумма",
        callback_data="withdrawal:amount:custom"
    ))
    
    builder.adjust(1)
    
    # Назад
    builder.row(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="withdrawal:menu"
    ))
    
    return builder.as_markup()


def get_withdrawal_confirm_keyboard(
    withdrawal_id: int
) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения вывода.
    
    Args:
        withdrawal_id: ID вывода
        
    Returns:
        Keyboard с подтверждением
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="✅ Подтвердить",
        callback_data=f"withdrawal:finpass:{withdrawal_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="✏️ Изменить сумму",
        callback_data="withdrawal:new"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Отменить",
        callback_data=f"withdrawal:cancel:{withdrawal_id}"
    ))
    
    builder.adjust(1)
    return builder.as_markup()
```

**Файл: `app/bot/keyboards/referral.py`**
```python
"""Referral keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_referral_menu() -> InlineKeyboardMarkup:
    """Меню реферальной системы."""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="🔗 Моя ссылка",
        callback_data="referral:link"
    ))
    builder.add(InlineKeyboardButton(
        text="📊 Статистика",
        callback_data="referral:stats"
    ))
    builder.add(InlineKeyboardButton(
        text="🌳 Дерево рефералов",
        callback_data="referral:tree"
    ))
    builder.add(InlineKeyboardButton(
        text="💰 Заработано",
        callback_data="referral:earnings"
    ))
    builder.add(InlineKeyboardButton(
        text="❓ Как это работает",
        callback_data="referral:help"
    ))
    
    builder.adjust(2)
    return builder.as_markup()


def get_referral_tree_keyboard(
    level: int = 1,
    max_level: int = 3
) -> InlineKeyboardMarkup:
    """
    Клавиатура навигации по дереву рефералов.
    
    Args:
        level: Текущий уровень
        max_level: Максимальный уровень
        
    Returns:
        Keyboard с уровнями
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопки уровней
    for lvl in range(1, max_level + 1):
        emoji = "📍" if lvl == level else "⚪"
        builder.add(InlineKeyboardButton(
            text=f"{emoji} Уровень {lvl}",
            callback_data=f"referral:tree:{lvl}"
        ))
    
    builder.adjust(3)
    
    # Назад
    builder.row(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="referral:menu"
    ))
    
    return builder.as_markup()
```

**Файл: `app/bot/keyboards/admin.py`**
```python
"""Admin keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_menu() -> InlineKeyboardMarkup:
    """Главное меню админки."""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="📊 Статистика",
        callback_data="admin:stats"
    ))
    builder.add(InlineKeyboardButton(
        text="👥 Пользователи",
        callback_data="admin:users"
    ))
    builder.add(InlineKeyboardButton(
        text="💰 Финансы",
        callback_data="admin:finance"
    ))
    builder.add(InlineKeyboardButton(
        text="📢 Рассылка",
        callback_data="admin:broadcast"
    ))
    builder.add(InlineKeyboardButton(
        text="⚙️ Настройки",
        callback_data="admin:settings"
    ))
    builder.add(InlineKeyboardButton(
        text="🚫 Блэклист",
        callback_data="admin:blacklist"
    ))
    builder.add(InlineKeyboardButton(
        text="🎫 Тикеты",
        callback_data="admin:tickets"
    ))
    builder.add(InlineKeyboardButton(
        text="📝 Логи",
        callback_data="admin:logs"
    ))
    
    builder.adjust(2)
    return builder.as_markup()


def get_admin_user_actions(
    user_id: int,
    is_banned: bool = False
) -> InlineKeyboardMarkup:
    """
    Действия с пользователем.
    
    Args:
        user_id: ID пользователя
        is_banned: Забанен ли
        
    Returns:
        Keyboard с действиями
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="📊 Информация",
        callback_data=f"admin:user:info:{user_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="💰 Баланс",
        callback_data=f"admin:user:balance:{user_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="📝 История",
        callback_data=f"admin:user:history:{user_id}"
    ))
    
    if is_banned:
        builder.add(InlineKeyboardButton(
            text="✅ Разбанить",
            callback_data=f"admin:user:unban:{user_id}"
        ))
    else:
        builder.add(InlineKeyboardButton(
            text="🚫 Забанить",
            callback_data=f"admin:user:ban:{user_id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="💬 Написать",
        callback_data=f"admin:user:message:{user_id}"
    ))
    
    builder.adjust(2)
    
    # Назад
    builder.row(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="admin:users"
    ))
    
    return builder.as_markup()


def get_broadcast_confirm(
    total_users: int
) -> InlineKeyboardMarkup:
    """
    Подтверждение рассылки.
    
    Args:
        total_users: Количество пользователей
        
    Returns:
        Keyboard с подтверждением
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text=f"✅ Отправить {total_users} пользователям",
        callback_data="admin:broadcast:confirm"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Отменить",
        callback_data="admin:broadcast:cancel"
    ))
    
    builder.adjust(1)
    return builder.as_markup()
```

**Файл: `app/bot/keyboards/support.py`**
```python
"""Support keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_support_menu() -> InlineKeyboardMarkup:
    """Меню поддержки."""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="✉️ Новое обращение",
        callback_data="support:new"
    ))
    builder.add(InlineKeyboardButton(
        text="📋 Мои обращения",
        callback_data="support:list"
    ))
    builder.add(InlineKeyboardButton(
        text="❓ FAQ",
        callback_data="support:faq"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_support_categories() -> InlineKeyboardMarkup:
    """Категории обращений."""
    builder = InlineKeyboardBuilder()
    
    categories = [
        ("💰 Финансы", "support:category:finance"),
        ("🔧 Технические", "support:category:technical"),
        ("👥 Рефералы", "support:category:referral"),
        ("❓ Другое", "support:category:other"),
    ]
    
    for text, callback_data in categories:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        ))
    
    builder.adjust(1)
    
    # Назад
    builder.row(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="support:menu"
    ))
    
    return builder.as_markup()


def get_ticket_actions(
    ticket_id: int,
    status: str
) -> InlineKeyboardMarkup:
    """
    Действия с тикетом.
    
    Args:
        ticket_id: ID тикета
        status: Статус тикета
        
    Returns:
        Keyboard с действиями
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="💬 Ответить",
        callback_data=f"support:reply:{ticket_id}"
    ))
    
    if status != "closed":
        builder.add(InlineKeyboardButton(
            text="✅ Закрыть",
            callback_data=f"support:close:{ticket_id}"
        ))
    
    builder.adjust(1)
    
    # Назад
    builder.row(InlineKeyboardButton(
        text="◀️ К списку",
        callback_data="support:list"
    ))
    
    return builder.as_markup()
```

**Файл: `app/bot/keyboards/pagination.py`**
```python
"""Pagination helper."""
from typing import List, Callable
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def paginate(
    items: List,
    page: int,
    per_page: int,
    callback_prefix: str,
    item_formatter: Callable
) -> InlineKeyboardMarkup:
    """
    Универсальная пагинация.
    
    Args:
        items: Список элементов
        page: Номер страницы
        per_page: Элементов на странице
        callback_prefix: Префикс callback
        item_formatter: Функция форматирования элемента
        
    Returns:
        Keyboard с пагинацией
    """
    builder = InlineKeyboardBuilder()
    
    total_pages = (len(items) + per_page - 1) // per_page
    start = page * per_page
    end = start + per_page
    
    # Элементы текущей страницы
    for item in items[start:end]:
        text, callback_data = item_formatter(item)
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        ))
    
    builder.adjust(1)
    
    # Навигация
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️",
            callback_data=f"{callback_prefix}:{page-1}"
        ))
    
    nav_buttons.append(InlineKeyboardButton(
        text=f"{page+1}/{total_pages}",
        callback_data="noop"
    ))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="▶️",
            callback_data=f"{callback_prefix}:{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    return builder.as_markup()
```

---

## 🛡️ МОДУЛЬ 11: Middlewares (ПОЛНАЯ РЕАЛИЗАЦИЯ)

**Файл: `app/bot/middlewares/logging.py`**
```python
"""Logging middleware."""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Update, TelegramObject
from loguru import logger


class LoggingMiddleware(BaseMiddleware):
    """Логирование всех событий."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Логирование события.
        
        Args:
            handler: Следующий handler
            event: Telegram событие
            data: Данные
            
        Returns:
            Результат handler
        """
        update: Update = data.get("event_update")
        
        if update.message:
            logger.info(
                f"Message from {update.message.from_user.id}: "
                f"{update.message.text}"
            )
        elif update.callback_query:
            logger.info(
                f"Callback from {update.callback_query.from_user.id}: "
                f"{update.callback_query.data}"
            )
        
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error handling update: {e}", exc_info=True)
            raise
```

**Файл: `app/bot/middlewares/auth.py`**
```python
"""Authentication middleware."""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from loguru import logger

from app.services.user.user_service import UserService
from app.core.exceptions import UserNotFound


class AuthMiddleware(BaseMiddleware):
    """Проверка регистрации пользователя."""
    
    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Проверка пользователя.
        
        Args:
            handler: Следующий handler
            event: Telegram событие
            data: Данные
            
        Returns:
            Результат handler
        """
        # Получение telegram_id
        telegram_id = None
        if isinstance(event, Message):
            telegram_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            telegram_id = event.from_user.id
        
        if telegram_id:
            try:
                # Получение пользователя
                user = await self.user_service.get_by_telegram_id(
                    telegram_id
                )
                
                # Добавление в data
                data["user"] = user
                data["user_id"] = user.id
                
                logger.debug(f"User {user.id} authenticated")
                
            except UserNotFound:
                # Пользователь не зарегистрирован
                logger.warning(
                    f"User {telegram_id} not registered"
                )
                data["user"] = None
                data["user_id"] = None
        
        return await handler(event, data)
```

**Файл: `app/bot/middlewares/admin.py`**
```python
"""Admin check middleware."""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.core.config import settings


class AdminMiddleware(BaseMiddleware):
    """Проверка прав админа."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Проверка админа.
        
        Args:
            handler: Следующий handler
            event: Telegram событие
            data: Данные
            
        Returns:
            Результат handler или None
        """
        telegram_id = None
        if isinstance(event, Message):
            telegram_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            telegram_id = event.from_user.id
        
        # Проверка admin ID
        is_admin = telegram_id in settings.TELEGRAM_ADMIN_IDS
        data["is_admin"] = is_admin
        
        if not is_admin:
            # Отклонение доступа
            if isinstance(event, Message):
                await event.answer(
                    "❌ У вас нет доступа к этой команде."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "❌ У вас нет доступа",
                    show_alert=True
                )
            return None
        
        return await handler(event, data)
```

**Файл: `app/bot/middlewares/throttling.py`**
```python
"""Throttling (rate limiting) middleware."""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import time

from app.core.config import settings


class ThrottlingMiddleware(BaseMiddleware):
    """
    Rate limiting пользователей.
    
    Ограничивает количество запросов от одного пользователя.
    """
    
    def __init__(self, rate_limit: int = 20) -> None:
        """
        Инициализация.
        
        Args:
            rate_limit: Запросов в минуту
        """
        self.rate_limit = rate_limit
        self.user_requests: Dict[int, list] = {}
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Проверка rate limit.
        
        Args:
            handler: Следующий handler
            event: Telegram событие
            data: Данные
            
        Returns:
            Результат handler или None
        """
        if not settings.RATE_LIMIT_ENABLED:
            return await handler(event, data)
        
        telegram_id = None
        if isinstance(event, Message):
            telegram_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            telegram_id = event.from_user.id
        
        if not telegram_id:
            return await handler(event, data)
        
        current_time = time.time()
        
        # Получение истории запросов
        if telegram_id not in self.user_requests:
            self.user_requests[telegram_id] = []
        
        requests = self.user_requests[telegram_id]
        
        # Очистка старых запросов (старше 1 минуты)
        requests = [
            req_time for req_time in requests 
            if current_time - req_time < 60
        ]
        self.user_requests[telegram_id] = requests
        
        # Проверка лимита
        if len(requests) >= self.rate_limit:
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ Слишком много запросов. "
                    "Пожалуйста, подождите минуту."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "⚠️ Слишком много запросов",
                    show_alert=True
                )
            return None
        
        # Добавление текущего запроса
        requests.append(current_time)
        
        return await handler(event, data)
```

**Файл: `app/bot/middlewares/db_session.py`**
```python
"""Database session middleware."""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database.session import async_session_maker


class DatabaseSessionMiddleware(BaseMiddleware):
    """Инъекция database session в handlers."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Создание и инъекция session.
        
        Args:
            handler: Следующий handler
            event: Telegram событие
            data: Данные
            
        Returns:
            Результат handler
        """
        async with async_session_maker() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
```

---

## 🎯 МОДУЛЬ 12: Filters (ПОЛНАЯ РЕАЛИЗАЦИЯ)

**Файл: `app/bot/filters/admin.py`**
```python
"""Admin filter."""
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery

from app.core.config import settings


class IsAdmin(Filter):
    """Фильтр для админов."""
    
    async def __call__(
        self, 
        obj: Message | CallbackQuery
    ) -> bool:
        """
        Проверка админа.
        
        Args:
            obj: Message или CallbackQuery
            
        Returns:
            True если админ
        """
        user_id = obj.from_user.id
        return user_id in settings.TELEGRAM_ADMIN_IDS
```

**Файл: `app/bot/filters/registered.py`**
```python
"""Registered user filter."""
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery


class IsRegistered(Filter):
    """Фильтр зарегистрированных пользователей."""
    
    async def __call__(
        self, 
        obj: Message | CallbackQuery,
        user: dict | None = None
    ) -> bool:
        """
        Проверка регистрации.
        
        Args:
            obj: Message или CallbackQuery
            user: User из middleware
            
        Returns:
            True если зарегистрирован
        """
        return user is not None
```

**Файл: `app/bot/filters/chat_type.py`**
```python
"""Chat type filter."""
from typing import Union
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery


class ChatTypeFilter(Filter):
    """Фильтр типа чата."""
    
    def __init__(self, chat_type: Union[str, list[str]]) -> None:
        """
        Инициализация.
        
        Args:
            chat_type: Тип чата ('private', 'group', etc)
        """
        if isinstance(chat_type, str):
            self.chat_types = [chat_type]
        else:
            self.chat_types = chat_type
    
    async def __call__(self, message: Message) -> bool:
        """
        Проверка типа чата.
        
        Args:
            message: Сообщение
            
        Returns:
            True если тип совпадает
        """
        return message.chat.type in self.chat_types
```

---

## 🔄 МОДУЛЬ 13: FSM States (ПОЛНАЯ РЕАЛИЗАЦИЯ)

**Файл: `app/bot/states/deposit.py`**
```python
"""Deposit FSM states."""
from aiogram.fsm.state import State, StatesGroup


class DepositStates(StatesGroup):
    """Состояния процесса депозита."""
    
    waiting_for_amount = State()  # Ожидание суммы
    waiting_for_confirmation = State()  # Ожидание подтверждения
```

**Файл: `app/bot/states/withdrawal.py`**
```python
"""Withdrawal FSM states."""
from aiogram.fsm.state import State, StatesGroup


class WithdrawalStates(StatesGroup):
    """Состояния процесса вывода."""
    
    waiting_for_amount = State()  # Ожидание суммы
    waiting_for_address = State()  # Ожидание адреса
    waiting_for_finpass = State()  # Ожидание finpass
    waiting_for_confirmation = State()  # Ожидание подтверждения
```

**Файл: `app/bot/states/support.py`**
```python
"""Support FSM states."""
from aiogram.fsm.state import State, StatesGroup


class SupportStates(StatesGroup):
    """Состояния создания тикета."""
    
    waiting_for_category = State()  # Ожидание категории
    waiting_for_subject = State()  # Ожидание темы
    waiting_for_message = State()  # Ожидание сообщения


class TicketReplyStates(StatesGroup):
    """Состояния ответа на тикет."""
    
    waiting_for_reply = State()  # Ожидание ответа
```

**Файл: `app/bot/states/admin.py`**
```python
"""Admin FSM states."""
from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    """Состояния рассылки."""
    
    waiting_for_message = State()  # Ожидание текста
    waiting_for_image = State()  # Ожидание картинки (опц.)
    waiting_for_button = State()  # Ожидание кнопки (опц.)
    waiting_for_confirmation = State()  # Ожидание подтверждения


class UserEditStates(StatesGroup):
    """Состояния редактирования пользователя."""
    
    waiting_for_user_id = State()  # Ожидание ID
    waiting_for_field = State()  # Ожидание поля
    waiting_for_value = State()  # Ожидание значения


class SettingsEditStates(StatesGroup):
    """Состояния редактирования настроек."""
    
    waiting_for_key = State()  # Ожидание ключа
    waiting_for_value = State()  # Ожидание значения
```

---

## ⚠️ МОДУЛЬ 14: Error Handlers (КРИТИЧНО!)

**Файл: `app/bot/handlers/error.py`**
```python
"""Global error handler."""
from aiogram import Router
from aiogram.types import ErrorEvent
from loguru import logger

from app.core.exceptions import (
    UserNotFound,
    InsufficientBalance,
    InvalidAmount,
    WithdrawalLimitExceeded
)

router = Router(name="errors")


@router.errors()
async def global_error_handler(event: ErrorEvent) -> None:
    """
    Глобальный обработчик ошибок.
    
    Args:
        event: Событие ошибки
    """
    logger.error(
        f"Error in update {event.update.update_id}: "
        f"{event.exception}",
        exc_info=True
    )
    
    # Получение объекта для ответа
    obj = None
    if event.update.message:
        obj = event.update.message
    elif event.update.callback_query:
        obj = event.update.callback_query
    
    if not obj:
        return
    
    # Обработка специфичных ошибок
    exception = event.exception
    
    if isinstance(exception, UserNotFound):
        await obj.answer(
            "❌ Пользователь не найден. "
            "Используйте /start для регистрации."
        )
    
    elif isinstance(exception, InsufficientBalance):
        await obj.answer(
            "❌ Недостаточно средств на балансе."
        )
    
    elif isinstance(exception, InvalidAmount):
        await obj.answer(
            "❌ Неверная сумма. Пожалуйста, попробуйте снова."
        )
    
    elif isinstance(exception, WithdrawalLimitExceeded):
        await obj.answer(
            "❌ Превышен лимит на вывод средств."
        )
    
    else:
        # Общая ошибка
        await obj.answer(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже "
            "или обратитесь в поддержку."
        )
```

---

## 🔐 МОДУЛЬ 15: Custom Exceptions (ПОЛНАЯ РЕАЛИЗАЦИЯ)

**Файл: `app/core/exceptions.py`**
```python
"""Custom exceptions."""


class AppException(Exception):
    """Базовое исключение приложения."""
    
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class UserNotFound(AppException):
    """Пользователь не найден."""
    pass


class UserAlreadyExists(AppException):
    """Пользователь уже существует."""
    pass


class InsufficientBalance(AppException):
    """Недостаточно средств."""
    pass


class InvalidAmount(AppException):
    """Неверная сумма."""
    pass


class WithdrawalLimitExceeded(AppException):
    """Превышен лимит вывода."""
    pass


class DepositNotFound(AppException):
    """Депозит не найден."""
    pass


class WithdrawalNotFound(AppException):
    """Вывод не найден."""
    pass


class InvalidFinancialPassword(AppException):
    """Неверный финансовый пароль."""
    pass


class FinancialPasswordLocked(AppException):
    """Финансовый пароль заблокирован."""
    pass


class InvalidAddress(AppException):
    """Неверный адрес кошелька."""
    pass


class TransactionFailed(AppException):
    """Транзакция провалилась."""
    pass


class RateLimitExceeded(AppException):
    """Превышен rate limit."""
    pass


class TicketNotFound(AppException):
    """Тикет не найден."""
    pass


class TicketClosed(AppException):
    """Тикет закрыт."""
    pass


class UnauthorizedAccess(AppException):
    """Неавторизованный доступ."""
    pass


class ConfigurationError(AppException):
    """Ошибка конфигурации."""
    pass
```

---

**ПРОДОЛЖЕНИЕ В ЧАСТИ 4 из-за ограничения размера файла...**

Создать ЧАСТЬ 4 с остальными модулями:
- Utils (форматтеры, валидаторы)
- Constants и Enums
- Alembic migrations setup
- Loguru setup
- Health checks
- Graceful shutdown
- Audit logging
- Performance monitoring
- Rate limiting implementation
- Cache layer
- Backup scripts
- Docker secrets
- Environment validation
- Testing utilities

Продолжить?



