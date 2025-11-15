"""
Menu buttons constants.

Centralized list of menu button texts to prevent handlers from intercepting them.
"""

# Main menu buttons
MAIN_MENU_BUTTONS = [
    "💰 Депозит",
    "💸 Вывод",
    "👥 Рефералы",
    "📊 Баланс",
    "🎁 Награды",
    "📜 История",
    "💬 Поддержка",
    "⚙️ Настройки",
    "✅ Пройти верификацию",
    "📝 Подать апелляцию",
    "📊 Главное меню",
    "◀️ Назад",
    "◀️ Главное меню",
]

# Support menu buttons
SUPPORT_MENU_BUTTONS = [
    "✉️ Создать обращение",
    "📋 Мои обращения",
    "❓ FAQ",
    "◀️ Назад",
]

# All menu buttons
ALL_MENU_BUTTONS = MAIN_MENU_BUTTONS + SUPPORT_MENU_BUTTONS


def is_menu_button(text: str) -> bool:
    """
    Check if text is a menu button.
    
    Args:
        text: Message text to check
        
    Returns:
        True if text is a menu button, False otherwise
    """
    return text in ALL_MENU_BUTTONS

