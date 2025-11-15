#!/bin/bash
###############################################################################
# Quick Deploy Script for SigmaTrade Bot
# Simplified deployment script for fast production setup
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

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║      SigmaTrade Bot - Quick Deploy Script            ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Check readiness
log "Step 1/5: Checking readiness..."
if ! "${PROJECT_ROOT}/scripts/check-readiness.sh"; then
    error "Readiness check failed. Please fix errors and try again."
    exit 1
fi

# Step 2: Setup environment (if needed)
log "Step 2/5: Setting up environment..."
if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    info ".env file not found, running setup..."
    "${PROJECT_ROOT}/scripts/setup-env.sh"
    
    warn "⚠️  Please edit .env file and fill in all required values:"
    echo "  nano ${PROJECT_ROOT}/.env"
    echo ""
    read -p "Press Enter when .env is configured..."
fi

# Step 3: Validate environment
log "Step 3/5: Validating environment..."
if ! python3 "${PROJECT_ROOT}/scripts/validate-env.py"; then
    error "Environment validation failed"
    exit 1
fi

# Step 4: Build and start Docker containers
log "Step 4/5: Building and starting Docker containers..."
cd "${PROJECT_ROOT}"

if docker-compose -f docker-compose.python.yml build; then
    log "✅ Docker images built successfully"
else
    error "Docker build failed"
    exit 1
fi

if docker-compose -f docker-compose.python.yml up -d; then
    log "✅ Docker containers started"
else
    error "Failed to start Docker containers"
    exit 1
fi

# Step 5: Verify deployment
log "Step 5/5: Verifying deployment..."
sleep 5

info "Checking container status..."
docker-compose -f docker-compose.python.yml ps

info "Checking bot logs (last 20 lines)..."
docker-compose -f docker-compose.python.yml logs bot | tail -20

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Deployment Complete!                       ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

log "✅ Bot is deployed and running!"
info ""
info "Useful commands:"
info "  - View logs: docker-compose -f docker-compose.python.yml logs -f bot"
info "  - Stop: docker-compose -f docker-compose.python.yml down"
info "  - Restart: docker-compose -f docker-compose.python.yml restart"
info ""
info "Test the bot by sending /start in Telegram"

