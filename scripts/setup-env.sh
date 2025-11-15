#!/bin/bash
###############################################################################
# Environment Setup Script for SigmaTrade Bot
# Automates .env file creation and validation
###############################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[$(date +'%H:%M:%S')] ERROR:${NC} $1" >&2; }
warn() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING:${NC} $1"; }
info() { echo -e "${BLUE}[$(date +'%H:%M:%S')] INFO:${NC} $1"; }

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║      SigmaTrade Bot - Environment Setup Script       ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env.example exists
if [ ! -f "${ENV_EXAMPLE}" ]; then
    error ".env.example not found at ${ENV_EXAMPLE}"
    exit 1
fi

# Step 1: Create .env from .env.example if it doesn't exist
if [ -f "${ENV_FILE}" ]; then
    warn ".env file already exists"
    read -p "Do you want to overwrite it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Keeping existing .env file"
    else
        log "Backing up existing .env to .env.backup"
        cp "${ENV_FILE}" "${ENV_FILE}.backup"
        cp "${ENV_EXAMPLE}" "${ENV_FILE}"
        log ".env file created from .env.example"
    fi
else
    cp "${ENV_EXAMPLE}" "${ENV_FILE}"
    log ".env file created from .env.example"
fi

# Step 2: Generate secrets if not set
log "Checking and generating secrets..."

# Generate SECRET_KEY if not set or is placeholder
if grep -q "your_secret_key_here" "${ENV_FILE}" || ! grep -q "^SECRET_KEY=" "${ENV_FILE}"; then
    SECRET_KEY=$(openssl rand -hex 32)
    if grep -q "^SECRET_KEY=" "${ENV_FILE}"; then
        sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" "${ENV_FILE}"
    else
        echo "SECRET_KEY=${SECRET_KEY}" >> "${ENV_FILE}"
    fi
    log "Generated SECRET_KEY"
fi

# Generate ENCRYPTION_KEY if not set or is placeholder
if grep -q "your_encryption_key_here" "${ENV_FILE}" || ! grep -q "^ENCRYPTION_KEY=" "${ENV_FILE}"; then
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    if grep -q "^ENCRYPTION_KEY=" "${ENV_FILE}"; then
        sed -i "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=${ENCRYPTION_KEY}|" "${ENV_FILE}"
    else
        echo "ENCRYPTION_KEY=${ENCRYPTION_KEY}" >> "${ENV_FILE}"
    fi
    log "Generated ENCRYPTION_KEY"
fi

# Step 3: Set file permissions
chmod 600 "${ENV_FILE}"
log "Set .env file permissions to 600"

# Step 4: Validate required variables
log "Validating required environment variables..."

REQUIRED_VARS=(
    "TELEGRAM_BOT_TOKEN"
    "DATABASE_URL"
    "WALLET_PRIVATE_KEY"
    "WALLET_ADDRESS"
    "USDT_CONTRACT_ADDRESS"
    "RPC_URL"
    "SYSTEM_WALLET_ADDRESS"
    "SECRET_KEY"
    "ENCRYPTION_KEY"
)

MISSING_VARS=()
PLACEHOLDER_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" "${ENV_FILE}"; then
        MISSING_VARS+=("${var}")
    elif grep -q "^${var}=.*your_.*" "${ENV_FILE}" || grep -q "^${var}=$" "${ENV_FILE}"; then
        PLACEHOLDER_VARS+=("${var}")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ] || [ ${#PLACEHOLDER_VARS[@]} -gt 0 ]; then
    warn "Some required variables need to be configured:"
    
    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        error "Missing variables:"
        for var in "${MISSING_VARS[@]}"; do
            echo "  - ${var}"
        done
    fi
    
    if [ ${#PLACEHOLDER_VARS[@]} -gt 0 ]; then
        warn "Variables with placeholder values:"
        for var in "${PLACEHOLDER_VARS[@]}"; do
            echo "  - ${var}"
        done
    fi
    
    echo ""
    info "Please edit .env file and fill in all required values:"
    echo "  nano ${ENV_FILE}"
    echo ""
    warn "⚠️  Bot will not start until all required variables are configured!"
else
    log "✅ All required variables are configured"
fi

# Step 5: Summary
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Environment Setup Complete!               ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

if [ ${#MISSING_VARS[@]} -eq 0 ] && [ ${#PLACEHOLDER_VARS[@]} -eq 0 ]; then
    log "✅ Environment is ready for deployment"
    log "You can now run: docker-compose -f docker-compose.python.yml up -d"
else
    warn "⚠️  Please configure missing variables before deployment"
fi

