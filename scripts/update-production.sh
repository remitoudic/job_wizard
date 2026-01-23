#!/usr/bin/env bash
# Safe production update script with automatic backup and rollback
# Use this to deploy new code from GitHub to production

set -euo pipefail

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
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 1
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
if command -v docker-compose > /dev/null 2>&1; then
    docker-compose up -d --build
else
    docker compose up -d --build
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
CONTAINERS=("jobwizard-postgres" "jobwizard-ollama" "jobwizard-backend" "jobwizard-frontend")
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
if curl -s --max-time 5 http://localhost:8000/health > /dev/null 2>&1 || \
   curl -s --max-time 5 http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✅ Backend API is responding"
else
    echo "   ❌ Backend API is not responding"
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
    echo "   Frontend: http://${EXPECTED_IP}:5173"
    echo "   Backend:  http://${EXPECTED_IP}:8000"
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
        docker-compose up -d --build
    else
        docker compose up -d --build
    fi
    
    echo ""
    echo "✅ Rolled back to commit: ${CURRENT_COMMIT:0:8}"
    echo ""
    echo "⚠️  Please check the logs to diagnose the issue:"
    echo "   docker compose logs backend"
    echo "   docker compose logs frontend"
    exit 1
fi
