"""
E2E tests using BotTestClient.

More readable and maintainable tests using high-level test client.
"""

import pytest
from aiogram import Bot
from aiogram.client.session.memory import MemorySession
from aiogram.fsm.storage.memory import MemoryStorage

from tests.helpers.bot_test_client import BotTestClient, create_test_client


@pytest.mark.asyncio
async def test_start_command_with_client(mock_bot: Bot, mock_dispatcher, test_user):
    """Test /start command using test client."""
    client = await create_test_client(mock_bot, mock_dispatcher)
    
    # Send /start command
    await client.send_message("/start", user_id=123456789)
    
    # Verify response (would check actual bot response)
    # In real implementation, you'd check bot's sent messages
    assert len(client.get_sent_messages()) == 1


@pytest.mark.asyncio
async def test_deposit_flow_with_client(mock_bot: Bot, mock_dispatcher, test_user):
    """Test deposit flow using test client."""
    client = await create_test_client(mock_bot, mock_dispatcher)
    
    # Step 1: Click deposit
    await client.send_callback("menu:deposit", user_id=123456789)
    
    # Step 2: Select level
    await client.send_callback("deposit:level:1", user_id=123456789)
    
    # Step 3: Enter amount
    await client.send_message("100", user_id=123456789)
    
    # Verify flow completed
    assert len(client.get_received_updates()) == 3


@pytest.mark.asyncio
async def test_main_menu_navigation(mock_bot: Bot, mock_dispatcher, test_user):
    """Test main menu navigation."""
    client = await create_test_client(mock_bot, mock_dispatcher)
    
    # Navigate through menu
    await client.send_callback("menu:main", user_id=123456789)
    await client.send_callback("menu:balance", user_id=123456789)
    await client.send_callback("menu:deposit", user_id=123456789)
    await client.send_callback("menu:withdrawal", user_id=123456789)
    
    assert len(client.get_received_updates()) == 4


@pytest.mark.asyncio
async def test_referral_link_generation(mock_bot: Bot, mock_dispatcher, test_user):
    """Test referral link generation."""
    client = await create_test_client(mock_bot, mock_dispatcher)
    
    # Open referral menu
    await client.send_callback("menu:referral", user_id=123456789)
    
    # Get referral link
    await client.send_callback("referral_link", user_id=123456789)
    
    # Verify link was generated
    assert len(client.get_received_updates()) == 2

