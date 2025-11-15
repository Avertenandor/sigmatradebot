"""
Simple bot tests without complex fixtures.

Tests basic functionality without requiring full e2e setup.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBotBasic:
    """Basic bot functionality tests."""
    
    def test_imports_work(self):
        """Test that all critical imports work."""
        # Test bot imports
        from bot.handlers import start, menu, deposit, withdrawal
        assert hasattr(start, 'router')
        assert hasattr(menu, 'router')
        assert hasattr(deposit, 'router')
        assert hasattr(withdrawal, 'router')
        
        # Test admin imports
        from bot.handlers.admin import panel, users, withdrawals
        assert hasattr(panel, 'router')
        assert hasattr(users, 'router')
        assert hasattr(withdrawals, 'router')
        
        # Test services
        from app.services import user_service, deposit_service, withdrawal_service
        assert user_service is not None
        assert deposit_service is not None
        assert withdrawal_service is not None
    
    def test_handlers_have_routers(self):
        """Test that all handlers have router attribute."""
        from bot.handlers import (
            start, menu, deposit, withdrawal, referral,
            profile, transaction, support
        )
        
        handlers = [start, menu, deposit, withdrawal, referral, profile, transaction, support]
        for handler in handlers:
            assert hasattr(handler, 'router'), f"{handler.__name__} missing router"
            assert handler.router is not None, f"{handler.__name__} router is None"
    
    def test_admin_handlers_have_routers(self):
        """Test that all admin handlers have router attribute."""
        from bot.handlers.admin import (
            panel, users, withdrawals, broadcast, wallet_key_setup
        )
        
        handlers = [panel, users, withdrawals, broadcast, wallet_key_setup]
        for handler in handlers:
            assert hasattr(handler, 'router'), f"{handler.__name__} missing router"
            assert handler.router is not None, f"{handler.__name__} router is None"
    
    def test_middlewares_import(self):
        """Test that middlewares can be imported."""
        from bot.middlewares import auth, database, request_id
        assert auth is not None
        assert database is not None
        assert request_id is not None
    
    def test_states_import(self):
        """Test that FSM states can be imported."""
        from bot.states.registration import RegistrationStates
        from bot.states.deposit import DepositStates
        from bot.states.withdrawal import WithdrawalStates
        
        assert RegistrationStates is not None
        assert DepositStates is not None
        assert WithdrawalStates is not None
    
    def test_services_import(self):
        """Test that services can be imported."""
        from app.services.user_service import UserService
        from app.services.deposit_service import DepositService
        from app.services.withdrawal_service import WithdrawalService
        
        assert UserService is not None
        assert DepositService is not None
        assert WithdrawalService is not None
    
    def test_models_import(self):
        """Test that models can be imported."""
        from app.models.user import User
        from app.models.deposit import Deposit
        from app.models.transaction import Transaction
        
        assert User is not None
        assert Deposit is not None
        assert Transaction is not None
    
    def test_repositories_import(self):
        """Test that repositories can be imported."""
        from app.repositories.user_repository import UserRepository
        from app.repositories.deposit_repository import DepositRepository
        
        assert UserRepository is not None
        assert DepositRepository is not None


class TestBotStructure:
    """Test bot structure and configuration."""
    
    def test_main_module_exists(self):
        """Test that bot.main module exists."""
        import bot.main
        assert hasattr(bot.main, 'main')
        assert callable(bot.main.main)
    
    def test_all_handlers_registered(self):
        """Test that all handlers are registered in main."""
        import inspect
        from bot import main
        
        # Read main.py to check handlers
        main_file = Path(__file__).parent.parent / "bot" / "main.py"
        content = main_file.read_text()
        
        # Check for key handlers
        assert "include_router(start.router)" in content
        assert "include_router(menu.router)" in content
        assert "include_router(deposit.router)" in content
        assert "include_router(withdrawal.router)" in content
        assert "include_router(finpass_recovery.router)" in content
        assert "include_router(instructions.router)" in content
    
    def test_admin_handlers_registered(self):
        """Test that all admin handlers are registered."""
        main_file = Path(__file__).parent.parent / "bot" / "main.py"
        content = main_file.read_text()
        
        # Check for admin handlers
        assert "include_router(panel.router)" in content
        assert "include_router(users.router)" in content
        assert "include_router(withdrawals.router)" in content
        assert "include_router(blacklist.router)" in content
        assert "include_router(wallet_key_setup.router)" in content

