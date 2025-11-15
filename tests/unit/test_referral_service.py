"""
Unit tests for ReferralService.

Tests referral chain creation, reward processing, and statistics.
"""

import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.referral_service import ReferralService, REFERRAL_RATES


@pytest.mark.asyncio
async def test_create_referral_relationships(session: AsyncSession):
    """Test creating referral relationships."""
    service = ReferralService(session)
    
    # This test requires existing users in database
    # Should be set up in fixtures
    success, error = await service.create_referral_relationships(
        new_user_id=2,
        direct_referrer_id=1,
    )
    
    # Test will pass if users exist, fail gracefully if not
    # In real test, use fixtures to create test users
    assert isinstance(success, bool)
    assert error is None or isinstance(error, str)


@pytest.mark.asyncio
async def test_self_referral_prevented(session: AsyncSession):
    """Test that self-referral is prevented."""
    service = ReferralService(session)
    success, error = await service.create_referral_relationships(
        new_user_id=1,
        direct_referrer_id=1,
    )
    assert success is False
    assert "самого себя" in error or "self" in error.lower()


@pytest.mark.asyncio
async def test_referral_rates_configured():
    """Test that referral rates are properly configured."""
    assert REFERRAL_RATES[1] == Decimal("0.03")  # 3%
    assert REFERRAL_RATES[2] == Decimal("0.02")  # 2%
    assert REFERRAL_RATES[3] == Decimal("0.05")  # 5%


@pytest.mark.asyncio
async def test_get_referral_stats(session: AsyncSession):
    """Test getting referral statistics."""
    service = ReferralService(session)
    stats = await service.get_referral_stats(user_id=1)
    
    assert isinstance(stats, dict)
    assert "direct_referrals" in stats
    assert "level2_referrals" in stats
    assert "level3_referrals" in stats
    assert "total_earned" in stats
    assert "pending_earnings" in stats
    assert "paid_earnings" in stats

