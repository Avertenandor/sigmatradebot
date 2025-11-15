"""
Admin States
FSM states for admin operations
"""

from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """States for admin operations"""

    # User management
    awaiting_user_to_ban = State()  # Legacy, kept for compatibility
    awaiting_user_to_block = State()  # Block user (with appeal)
    awaiting_user_to_terminate = State()  # Terminate user (no appeal)
    awaiting_user_to_unban = State()

    # Broadcast
    awaiting_broadcast_message = State()
    awaiting_user_message_target = State()
    awaiting_user_message_content = State()
