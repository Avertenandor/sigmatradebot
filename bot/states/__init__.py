"""
FSM States.

State groups for multi-step dialogs.
"""

from bot.states.deposit import DepositStates
from bot.states.registration import RegistrationStates
from bot.states.support import SupportStates
from bot.states.withdrawal import WithdrawalStates

__all__ = [
    "DepositStates",
    "RegistrationStates",
    "SupportStates",
    "WithdrawalStates",
]
