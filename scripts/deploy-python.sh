#!/bin/bash
###############################################################################
# Deployment Script for SigmaTrade Bot (Python) to Production
# Handles build, test, and deployment to production server
###############################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENVIRONMENT="${1:-production}"
SERVER_HOST="${SERVER_HOST:-your-server.com}"
SERVER_USER="${SERVER_USER:-deploy}"
SERVER_PATH="${SERVER_PATH:-/opt/sigmatradebot}"

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[$(date +'%H:%M:%S')] ERROR:${NC} $1" >&2; }
warn() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING:${NC} $1"; }
info() { echo -e "${BLUE}[$(date +'%H:%M:%S')] INFO:${NC} $1"; }

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║      SigmaTrade Bot (Python) Deployment Script      ║"
echo "║              Environment: ${ENVIRONMENT}                    ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    error "Invalid environment: ${ENVIRONMENT}"
    error "Valid options: development, staging, production"
    exit 1
fi

# Step 1: Pre-flight checks
log "Step 1/8: Running pre-flight checks..."

# Check required commands
REQUIRED_COMMANDS=("git" "docker" "docker-compose")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
        error "Required command not found: $cmd"
        exit 1
    fi
done

# Check if .env file exists (only required for development)
if [ "$ENVIRONMENT" = "development" ] && [ ! -f "${PROJECT_ROOT}/.env" ]; then
    error ".env file not found in development mode. Please create it from .env.example"
    exit 1
fi

# In production/staging, secrets should come from environment variables or Secret Manager
if [ "$ENVIRONMENT" != "development" ]; then
    info "Production/Staging mode: Using environment variables for secrets"
    if [ -f "${PROJECT_ROOT}/.env" ]; then
        warn "⚠️  Local .env file detected in production deploy. Secrets should be in environment variables!"
    fi
fi

# Check git status
cd "${PROJECT_ROOT}"
if [ -n "$(git status --porcelain)" ]; then
    warn "You have uncommitted changes:"
    git status --short
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 2: Run Python tests
log "Step 2/8: Running Python tests..."
if [ "$ENVIRONMENT" = "production" ]; then
    if python -m pytest tests/ -v --tb=short; then
        log "Tests passed"
    else
        error "Tests failed. Cannot deploy to production."
        exit 1
    fi
else
    warn "Skipping tests for non-production environment"
fi

# Step 3: Build Docker image
log "Step 3/8: Building Docker image..."
IMAGE_TAG="sigmatrade-bot:${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"
LATEST_TAG="sigmatrade-bot:${ENVIRONMENT}-latest"

if docker build -f Dockerfile.python -t "${IMAGE_TAG}" -t "${LATEST_TAG}" .; then
    log "Docker image built: ${IMAGE_TAG}"
else
    error "Docker build failed"
    exit 1
fi

# Step 4: Test Docker image
log "Step 4/8: Testing Docker image..."
if docker run --rm "${LATEST_TAG}" python -c "import bot; print('✅ Bot imports OK')"; then
    log "Docker image test passed"
else
    error "Docker image test failed"
    exit 1
fi

# Step 5: Deploy to server (if SERVER_HOST is set)
if [ -n "${SERVER_HOST}" ] && [ "${SERVER_HOST}" != "your-server.com" ]; then
    log "Step 5/8: Deploying to server..."
    
    # Create deployment script
    DEPLOY_SCRIPT="
        set -e
        cd ${SERVER_PATH} || exit 1
        
        echo 'Stopping services...'
        docker-compose -f docker-compose.python.yml down || true
        
        echo 'Pulling latest code...'
        git pull origin main || git pull origin master
        
        echo 'Loading new Docker image...'
        docker load < /tmp/sigmatrade-bot-image.tar || true
        
        echo 'Starting services...'
        docker-compose -f docker-compose.python.yml up -d
        
        echo 'Waiting for services to be healthy...'
        sleep 10
        
        echo 'Checking service status...'
        docker-compose -f docker-compose.python.yml ps
        
        echo 'Deployment successful!'
    "
    
    # Save image to tar
    docker save "${LATEST_TAG}" | gzip > /tmp/sigmatrade-bot-image.tar.gz
    
    # Copy to server
    scp /tmp/sigmatrade-bot-image.tar.gz "${SERVER_USER}@${SERVER_HOST}:/tmp/"
    
    # Execute deployment
    ssh "${SERVER_USER}@${SERVER_HOST}" "gunzip -c /tmp/sigmatrade-bot-image.tar.gz | docker load && ${DEPLOY_SCRIPT}"
    
    # Cleanup
    rm -f /tmp/sigmatrade-bot-image.tar.gz
    
    log "Deployment to server completed"
else
    warn "Step 5/8: Skipping server deployment (SERVER_HOST not configured)"
fi

# Step 6: Local deployment (docker-compose)
log "Step 6/8: Updating local docker-compose..."
if [ -f "docker-compose.python.yml" ]; then
    docker-compose -f docker-compose.python.yml down
    docker-compose -f docker-compose.python.yml up -d --build
    log "Local services updated"
else
    warn "docker-compose.python.yml not found, skipping local deployment"
fi

# Step 7: Health check
log "Step 7/8: Running health checks..."
sleep 5

# Check if bot container is running
if docker ps | grep -q sigmatrade-bot; then
    log "Bot container is running"
else
    error "Bot container is not running!"
    exit 1
fi

# Check if worker container is running
if docker ps | grep -q sigmatrade-worker; then
    log "Worker container is running"
else
    warn "Worker container is not running"
fi

# Step 8: Post-deployment verification
log "Step 8/8: Verifying deployment..."

# Check logs for errors
if docker logs sigmatrade-bot --tail 50 2>&1 | grep -i error; then
    warn "Found errors in bot logs, please check manually"
else
    log "No errors found in bot logs"
fi

# Success!
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║           Deployment Completed Successfully!         ║"
echo "║                                                       ║"
echo "║  Environment: ${ENVIRONMENT}                                ║"
echo "║  Image: ${IMAGE_TAG}                          ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

log "All done! 🎉"
log "To view logs: docker-compose -f docker-compose.python.yml logs -f"
exit 0

