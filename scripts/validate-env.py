#!/usr/bin/env python3
"""
Environment Variables Validation Script

Validates that all required environment variables are set and have valid values.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import Settings


def validate_env() -> Tuple[bool, List[str]]:
    """
    Validate environment variables.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        settings = Settings()
    except Exception as e:
        return False, [f"Failed to load settings: {str(e)}"]
    
    # Required string variables
    required_strings = [
        ("telegram_bot_token", "TELEGRAM_BOT_TOKEN"),
        ("database_url", "DATABASE_URL"),
        ("wallet_private_key", "WALLET_PRIVATE_KEY"),
        ("wallet_address", "WALLET_ADDRESS"),
        ("usdt_contract_address", "USDT_CONTRACT_ADDRESS"),
        ("rpc_url", "RPC_URL"),
        ("system_wallet_address", "SYSTEM_WALLET_ADDRESS"),
        ("secret_key", "SECRET_KEY"),
        ("encryption_key", "ENCRYPTION_KEY"),
    ]
    
    for attr_name, env_name in required_strings:
        value = getattr(settings, attr_name, None)
        if not value or value.strip() == "":
            errors.append(f"{env_name} is not set or empty")
        elif "your_" in value.lower() or "placeholder" in value.lower():
            errors.append(f"{env_name} contains placeholder value")
    
    # Validate wallet address format (basic check)
    if settings.wallet_address and not settings.wallet_address.startswith("0x"):
        errors.append("WALLET_ADDRESS should start with '0x'")
    
    if settings.system_wallet_address and not settings.system_wallet_address.startswith("0x"):
        errors.append("SYSTEM_WALLET_ADDRESS should start with '0x'")
    
    # Validate USDT contract address
    if settings.usdt_contract_address and not settings.usdt_contract_address.startswith("0x"):
        errors.append("USDT_CONTRACT_ADDRESS should start with '0x'")
    
    # Validate RPC URL
    if settings.rpc_url and not (settings.rpc_url.startswith("http://") or settings.rpc_url.startswith("https://")):
        errors.append("RPC_URL should be a valid HTTP/HTTPS URL")
    
    # Validate database URL
    if settings.database_url and "postgresql" not in settings.database_url.lower():
        errors.append("DATABASE_URL should be a PostgreSQL connection string")
    
    # Validate admin IDs
    admin_ids = settings.get_admin_ids()
    if not admin_ids:
        errors.append("ADMIN_TELEGRAM_IDS is not set or empty")
    
    # Validate Redis settings
    if not settings.redis_host:
        errors.append("REDIS_HOST is not set")
    
    if settings.redis_port <= 0 or settings.redis_port > 65535:
        errors.append("REDIS_PORT should be between 1 and 65535")
    
    return len(errors) == 0, errors


def main():
    """Main function."""
    import sys
    
    print("🔍 Validating environment variables...")
    print("")
    
    is_valid, errors = validate_env()
    
    if is_valid:
        print("✅ All environment variables are valid!")
        print("")
        print("Environment is ready for deployment.")
        return 0
    else:
        print("❌ Environment validation failed!")
        print("")
        print("Errors found:")
        for error in errors:
            print(f"  - {error}")
        print("")
        print("Please fix the errors and try again.")
        print("You can use scripts/setup-env.sh to help configure .env file.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

