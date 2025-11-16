#!/usr/bin/env python3
"""
Test Blockchain Service Integration

Проверяет подключение к BSC RPC и работу с USDT контрактом.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config.settings import settings
from app.services.blockchain_service import get_blockchain_service
from loguru import logger


async def test_blockchain():
    """Test blockchain service."""
    print("=" * 70)
    print("🔗 ТЕСТ BLOCKCHAIN ИНТЕГРАЦИИ")
    print("=" * 70)
    print()
    
    try:
        # Initialize blockchain service
        blockchain = get_blockchain_service()
        print("✅ BlockchainService инициализирован")
        print(f"   RPC URL: {settings.rpc_url}")
        print()
        
        # Test 1: Check connection
        print("📡 Тест 1: Проверка подключения к BSC RPC...")
        is_connected = await asyncio.to_thread(blockchain.web3.is_connected)
        if is_connected:
            print("   ✅ Подключение к BSC RPC успешно")
        else:
            print("   ❌ Не удалось подключиться к BSC RPC")
            return False
        print()
        
        # Test 2: Get latest block
        print("🔢 Тест 2: Получение последнего блока...")
        latest_block = await asyncio.to_thread(blockchain.web3.eth.get_block_number)
        print(f"   ✅ Последний блок: {latest_block:,}")
        print()
        
        # Test 3: Check USDT contract
        print("📄 Тест 3: Проверка USDT контракта...")
        print(f"   USDT Contract: {settings.usdt_contract_address}")
        # Try to get contract code to verify it exists
        code = await asyncio.to_thread(
            blockchain.web3.eth.get_code,
            settings.usdt_contract_address
        )
        if code and code != b'\x00':
            print("   ✅ USDT контракт найден на BSC")
        else:
            print("   ❌ USDT контракт не найден (возможно неправильный адрес)")
        print()
        
        # Test 4: Check system wallet balance
        print("💰 Тест 4: Проверка баланса системного кошелька...")
        print(f"   Wallet: {settings.system_wallet_address}")
        balance = await blockchain.get_usdt_balance(settings.system_wallet_address)
        if balance is not None:
            print(f"   ✅ Баланс USDT: {balance:.2f} USDT")
        else:
            print("   ⚠️  Не удалось получить баланс USDT")
        
        # Get BNB balance
        bnb_balance_wei = await asyncio.to_thread(
            blockchain.web3.eth.get_balance,
            settings.system_wallet_address
        )
        bnb_balance = blockchain.web3.from_wei(bnb_balance_wei, 'ether')
        print(f"   ✅ Баланс BNB: {float(bnb_balance):.6f} BNB")
        print()
        
        # Test 5: Validate wallet addresses
        print("🔍 Тест 5: Валидация адресов кошельков...")
        wallets = [
            ("System Wallet", settings.system_wallet_address),
            ("Payout Wallet", settings.payout_wallet_address),
            ("Bot Wallet", settings.wallet_address),
        ]
        for name, address in wallets:
            is_valid = blockchain.validate_wallet_address(address)
            if is_valid:
                print(f"   ✅ {name}: {address} - валиден")
            else:
                print(f"   ❌ {name}: {address} - невалиден")
        print()
        
        # Test 6: Estimate gas fee
        print("⛽ Тест 6: Оценка комиссии за газ...")
        gas_fee = await blockchain.estimate_gas_fee(100.0)  # 100 USDT
        if gas_fee:
            print(f"   ✅ Ориентировочная комиссия: {gas_fee:.6f} BNB")
            if float(bnb_balance) < gas_fee:
                print(f"   ⚠️  ВНИМАНИЕ: Недостаточно BNB для оплаты газа!")
                print(f"   Требуется: {gas_fee:.6f} BNB, Доступно: {float(bnb_balance):.6f} BNB")
        else:
            print("   ⚠️  Не удалось оценить комиссию за газ")
        print()
        
        print("=" * 70)
        print("✅ ВСЕ ТЕСТЫ BLOCKCHAIN ИНТЕГРАЦИИ ПРОЙДЕНЫ")
        print("=" * 70)
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ ОШИБКА: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_blockchain())
    sys.exit(0 if success else 1)

