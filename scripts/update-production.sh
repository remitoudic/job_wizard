#!/usr/bin/env bash
# Safe production update script with automatic backup and rollback
# Use this to deploy new code from GitHub to production

set -euo pipefail

# Default values
FORCE_YES=false

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -y|--yes) FORCE_YES=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Production Update - Job Wizard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verify we're on the production server
PUBLIC_IP=$(curl -s --max-time 5 https://ifconfig.me 2>/dev/null || echo "unknown")
EXPECTED_IP="147.93.111.113"

if [ "$PUBLIC_IP" != "$EXPECTED_IP" ]; then
    echo "⚠️  WARNING: This script is meant for production server ($EXPECTED_IP)"
    echo "   Current IP: $PUBLIC_IP"
    echo ""
    
    if [ "$FORCE_YES" = true ]; then
        echo "   Bypassing check due to -y flag."
    else
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cancelled."
            exit 1
        fi
    fi
fi

# Save current git commit for rollback
CURRENT_COMMIT=$(git rev-parse HEAD)
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current state:"
echo "   Branch: $CURRENT_BRANCH"
echo "   Commit: ${CURRENT_COMMIT:0:8}"
echo ""

# Phase 1: Backup
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 1: Backup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f scripts/backup-db.sh ]; then
    # Pass -y to backup script if it supports it, or assume it's safe
    ./scripts/backup-db.sh
else
    echo "⚠️  Warning: backup-db.sh not found, skipping database backup"
fi

echo ""

# Phase 2: Pull latest code
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 2: Pull latest code"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📥 Fetching from GitHub..."
git fetch origin

echo "🔄 Pulling latest changes..."
if ! git pull origin "$CURRENT_BRANCH"; then
    echo "❌ Git pull failed! Manual intervention required."
    exit 1
fi

NEW_COMMIT=$(git rev-parse HEAD)
if [ "$CURRENT_COMMIT" = "$NEW_COMMIT" ]; then
    echo "ℹ️  Already up to date. No changes to deploy."
    # We continue anyway to ensure infrastructure matches code (rebuild)
    # or exit? Usually for an "update" script, if code hasn't changed, we might still want to rebuild if env vars changed.
    # But usually we exit. Let's ask user? Or just exit.
    # The original script exited. I'll keep it, but maybe print a message.
    echo "   (Re-run with --rebuild-only if you want to force rebuild without code changes - feature not yet implemented, continuing to rebuild anyway to be safe? No, let's respect original logic but maybe we want to rebuild if env changed? For now, I'll stick to original logic but allow forcing via -y if I executed it? No, if git is same, usually no deploy needed.)"
    # Actually, let's just proceed to rebuild if the user explicitly wants to ensure state?
    # Original script: exits 0.
    echo "   Exiting."
    exit 0
fi

echo "✅ Updated to commit: ${NEW_COMMIT:0:8}"
echo ""

# Phase 3: Rebuild and restart services
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 3: Rebuild and restart services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "🐳 Rebuilding Docker containers..."
COMPOSE_FILE="docker-compose.prod.yml"

if command -v docker-compose > /dev/null 2>&1; then
    docker-compose -f "$COMPOSE_FILE" up -d --build
else
    docker compose -f "$COMPOSE_FILE" up -d --build
fi

echo ""
echo "⏳ Waiting for services to start (10 seconds)..."
sleep 10

# Phase 4: Health checks
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 4: Health checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

HEALTH_CHECKS_PASSED=true

# Check if containers are running
echo "🔍 Checking containers..."
# Updated container names to match docker-compose.prod.yml
CONTAINERS=("jobwizard-postgres-prod" "jobwizard-ollama-prod" "jobwizard-backend-prod" "jobwizard-frontend-prod")

for container in "${CONTAINERS[@]}"; do
    if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
        echo "   ✅ $container is running"
    else
        echo "   ❌ $container is NOT running"
        HEALTH_CHECKS_PASSED=false
    fi
done

# Check backend API
echo ""
echo "🔍 Checking backend API..."
# Production uses port 80 via nginx usually, but backend is internal 8000.
# Nginx exposes 80. Checks should attack localhost:80.
if curl -s --max-time 5 http://localhost/health > /dev/null 2>&1 || \
   curl -s --max-time 5 http://localhost/ > /dev/null 2>&1; then
    echo "   ✅ Application is responding (Nginx/Backend)"
else
    echo "   ❌ Application is not responding at http://localhost"
    # Try internal backend port if exposed or just fail
    HEALTH_CHECKS_PASSED=false
fi

echo ""

# Phase 5: Decision
if [ "$HEALTH_CHECKS_PASSED" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Deployment Successful!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🎉 Job Wizard has been updated successfully!"
    echo "   From: ${CURRENT_COMMIT:0:8}"
    echo "   To:   ${NEW_COMMIT:0:8}"
    echo ""
    echo "🌐 Access your application at:"
    echo "   Frontend: http://${EXPECTED_IP}" # Default usage of port 80
    echo ""
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Deployment Failed - Initiating Rollback"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "⏮️  Rolling back to previous version..."
    
    # Rollback code
    git reset --hard "$CURRENT_COMMIT"
    
    # Restart services
    if command -v docker-compose > /dev/null 2>&1; then
        docker-compose -f "$COMPOSE_FILE" up -d --build
    else
        docker compose -f "$COMPOSE_FILE" up -d --build
    fi
    
    echo ""
    echo "✅ Rolled back to commit: ${CURRENT_COMMIT:0:8}"
    echo ""
    echo "⚠️  Please check the logs to diagnose the issue:"
    echo "   docker compose -f $COMPOSE_FILE logs backend"
    echo "   docker compose -f $COMPOSE_FILE logs nginx"
    exit 1
fi
