#!/usr/bin/env bash
# Safe production update script with automatic backup and rollback
# Use this to deploy new code from GitHub to production (Single-Node Docker Swarm)
#
# Usage:
#   ./scripts/update-production.sh            # interactive
#   ./scripts/update-production.sh -y         # non-interactive (CI/CD)
#   ./scripts/update-production.sh -y -f      # force rebuild even if already up to date

set -euo pipefail

FORCE_YES=false
FORCE_REBUILD=false
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -y|--yes) FORCE_YES=true ;;
        -f|--force) FORCE_REBUILD=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Production Update - Job Wizard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

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

if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    exit 1
fi

SWARM_STATE=$(docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null || echo "inactive")
if [ "$SWARM_STATE" != "active" ]; then
    echo "❌ Error: Docker Swarm is not active. Run ./scripts/deploy_production.sh first."
    exit 1
fi

ENV_FILE=".env/.env.production"
if [ ! -f "$ENV_FILE" ] && [ -f .env.production ]; then
    ENV_FILE=".env.production"
fi
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: Missing $ENV_FILE"
    exit 1
fi

COMPOSE_FILE="docker-compose.prod.yml"
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "📍 Current state:"
echo "   Branch target: $DEPLOY_BRANCH"
echo "   Commit: ${CURRENT_COMMIT:0:8}"
echo ""

# Phase 1: Backup
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 1: Backup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f scripts/backup-db.sh ]; then
    ./scripts/backup-db.sh || echo "⚠️  Pre-flight backup skipped or failed"
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

echo "🔄 Checking out $DEPLOY_BRANCH..."
git checkout "$DEPLOY_BRANCH"
if ! git pull --ff-only origin "$DEPLOY_BRANCH"; then
    echo "❌ Git pull failed! Manual intervention required."
    exit 1
fi

NEW_COMMIT=$(git rev-parse HEAD)
if [ "$CURRENT_COMMIT" = "$NEW_COMMIT" ]; then
    echo "ℹ️  Already up to date at ${NEW_COMMIT:0:8}."

    if [ "$FORCE_REBUILD" = true ]; then
        echo "⚠️  Forcing rebuild due to --force flag..."
    else
        echo "   (Use --force to force rebuild without code changes)"
        echo "   Exiting."
        exit 0
    fi
fi

echo "✅ Updated to commit: ${NEW_COMMIT:0:8}"
echo ""

# Phase 3: Rebuild and rolling update via Swarm
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 3: Rebuild and Swarm rolling update"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📝 Loading environment from $ENV_FILE..."
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [ ! -d "./services/backups" ]; then
    echo "📂 Creating backups directory..."
    mkdir -p ./services/backups
    chmod 777 ./services/backups
fi

echo "🏗️  Building production images..."
docker compose -f "$COMPOSE_FILE" build

echo "🚀 Deploying stack (jobwizard)..."
docker stack deploy -c "$COMPOSE_FILE" jobwizard

echo "🔄 Forcing service updates to pick up new images..."
for svc in jobwizard_backend jobwizard_frontend jobwizard_nginx jobwizard_worker; do
    docker service update --force "$svc" 2>/dev/null || echo "   ⚠️  Could not force-update $svc (may not exist yet)"
done

echo ""
echo "⏳ Waiting for services to stabilize (20 seconds)..."
sleep 20

# Phase 4: Health checks
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 4: Health checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

HEALTH_CHECKS_PASSED=true

echo "🔍 Checking Swarm services..."
SERVICES=("jobwizard_postgres" "jobwizard_backend" "jobwizard_frontend" "jobwizard_nginx" "jobwizard_worker" "jobwizard_temporal")

for service in "${SERVICES[@]}"; do
    REPLICAS=$(docker service ls --filter "name=${service}" --format '{{.Replicas}}' 2>/dev/null || true)
    if [[ "$REPLICAS" =~ ^([0-9]+)/([0-9]+)$ ]] && [ "${BASH_REMATCH[1]}" -ge 1 ] && [ "${BASH_REMATCH[1]}" -eq "${BASH_REMATCH[2]}" ]; then
        echo "   ✅ $service ($REPLICAS)"
    else
        echo "   ❌ $service is NOT healthy (replicas: ${REPLICAS:-none})"
        HEALTH_CHECKS_PASSED=false
    fi
done

echo ""
echo "🔍 Checking application HTTP health..."
if curl -sf --max-time 10 http://localhost/health > /dev/null 2>&1 || \
   curl -sf --max-time 10 http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "   ✅ Application is responding"
else
    # Fallback: frontend health via nginx root
    if curl -sf --max-time 10 http://localhost/ > /dev/null 2>&1; then
        echo "   ✅ Application root is responding"
    else
        echo "   ❌ Application is not responding"
        HEALTH_CHECKS_PASSED=false
    fi
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
    docker stack services jobwizard
    echo ""
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Deployment Failed - Initiating Rollback"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "⏮️  Rolling back to previous version..."

    git reset --hard "$CURRENT_COMMIT"

    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a

    docker compose -f "$COMPOSE_FILE" build
    docker stack deploy -c "$COMPOSE_FILE" jobwizard
    for svc in jobwizard_backend jobwizard_frontend jobwizard_nginx jobwizard_worker; do
        docker service update --force "$svc" 2>/dev/null || true
    done

    echo ""
    echo "✅ Rolled back to commit: ${CURRENT_COMMIT:0:8}"
    echo ""
    echo "⚠️  Please check the logs to diagnose the issue:"
    echo "   docker service logs -f jobwizard_backend"
    echo "   docker service logs -f jobwizard_nginx"
    exit 1
fi
