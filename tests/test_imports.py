"""
Test all imports and connections in the bot.

This test verifies that all modules can be imported correctly
and that all dependencies are properly configured.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestImports:
    """Test that all modules can be imported."""

    def test_bot_main_imports(self):
        """Test bot.main imports."""
        from bot.main import main
        assert callable(main)

    def test_handlers_imports(self):
        """Test all handlers can be imported."""
        from bot.handlers import (
            deposit,
            finpass_recovery,
            instructions,
            menu,
            start,
            withdrawal,
            referral,
            profile,
            transaction,
            support,
        )
        assert hasattr(deposit, 'router')
        assert hasattr(finpass_recovery, 'router')
        assert hasattr(instructions, 'router')
        assert hasattr(menu, 'router')
        assert hasattr(start, 'router')
        assert hasattr(withdrawal, 'router')
        assert hasattr(referral, 'router')
        assert hasattr(profile, 'router')
        assert hasattr(transaction, 'router')
        assert hasattr(support, 'router')

    def test_admin_handlers_imports(self):
        """Test all admin handlers can be imported."""
        from bot.handlers.admin import (
            blacklist,
            broadcast,
            deposit_settings,
            finpass_recovery as admin_finpass,
            management,
            panel,
            users,
            wallets,
            wallet_key_setup,
            withdrawals,
        )
        assert hasattr(blacklist, 'router')
        assert hasattr(broadcast, 'router')
        assert hasattr(deposit_settings, 'router')
        assert hasattr(admin_finpass, 'router')
        assert hasattr(management, 'router')
        assert hasattr(panel, 'router')
        assert hasattr(users, 'router')
        assert hasattr(wallets, 'router')
        assert hasattr(wallet_key_setup, 'router')
        assert hasattr(withdrawals, 'router')

    def test_middlewares_imports(self):
        """Test all middlewares can be imported."""
        from bot.middlewares import (
            auth,
            ban_middleware,
            database,
            logger_middleware,
            rate_limit_middleware,
            request_id,
        )
        assert hasattr(auth, 'AuthMiddleware')
        assert hasattr(ban_middleware, 'BanMiddleware')
        assert hasattr(database, 'DatabaseMiddleware')
        assert hasattr(logger_middleware, 'LoggerMiddleware')
        assert hasattr(rate_limit_middleware, 'RateLimitMiddleware')
        assert hasattr(request_id, 'RequestIDMiddleware')

    def test_states_imports(self):
        """Test all FSM states can be imported."""
        from bot.states.admin import (
            AdminManagementStates,
            DepositSettingsStates,
            WalletManagementStates,
            BlacklistStates,
        )
        from bot.states.finpass_recovery import FinpassRecoveryStates
        from bot.states.deposit import DepositStates
        from bot.states.withdrawal import WithdrawalStates
        from bot.states.registration import RegistrationStates
        from bot.states.support import SupportStates

        assert AdminManagementStates
        assert DepositSettingsStates
        assert WalletManagementStates
        assert BlacklistStates
        assert FinpassRecoveryStates
        assert DepositStates
        assert WithdrawalStates
        assert RegistrationStates
        assert SupportStates

    def test_services_imports(self):
        """Test all services can be imported."""
        from app.services.blacklist_service import BlacklistService
        from app.services.finpass_recovery_service import FinpassRecoveryService
        from app.services.settings_service import SettingsService
        from app.services.wallet_admin_service import WalletAdminService
        from app.services.blockchain import (
            BlockchainService,
            ProviderManager,
            EventMonitor,
            DepositProcessor,
            PaymentSender,
        )

        assert BlacklistService
        assert FinpassRecoveryService
        assert SettingsService
        assert WalletAdminService
        assert BlockchainService
        assert ProviderManager
        assert EventMonitor
        assert DepositProcessor
        assert PaymentSender

    def test_utils_imports(self):
        """Test all utils can be imported."""
        from app.utils.encryption import encrypt_data, decrypt_data
        from app.utils.validation import validate_wallet_address, validate_amount

        assert callable(encrypt_data)
        assert callable(decrypt_data)
        assert callable(validate_wallet_address)
        assert callable(validate_amount)


class TestRouterRegistration:
    """Test that all routers are properly configured."""

    def test_all_handlers_have_routers(self):
        """Test that all handlers have router attribute."""
        from bot.handlers import (
            deposit,
            finpass_recovery,
            instructions,
            menu,
            start,
            withdrawal,
            referral,
            profile,
            transaction,
            support,
        )
        from bot.handlers.admin import (
            blacklist,
            broadcast,
            deposit_settings,
            finpass_recovery as admin_finpass,
            management,
            panel,
            users,
            wallets,
            wallet_key_setup,
            withdrawals,
        )

        handlers = [
            deposit, finpass_recovery, instructions, menu, start,
            withdrawal, referral, profile, transaction, support,
            blacklist, broadcast, deposit_settings, admin_finpass,
            management, panel, users, wallets, wallet_key_setup, withdrawals,
        ]

        for handler in handlers:
            assert hasattr(handler, 'router'), f"{handler.__name__} missing router"
            assert handler.router is not None, f"{handler.__name__} router is None"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

