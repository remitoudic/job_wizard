#!/usr/bin/env bash
# Production Deployment Script
# Run this on your production server to deploy Job Wizard

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Job Wizard - PRODUCTION DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "   Please install/start Docker and try again."
    exit 1
fi

# Determine location of environment files
ENV_FILE=".env/.env.production"
ENV_EXAMPLE=".env/.env.production.example"

if [ ! -f "$ENV_FILE" ] && [ -f .env.production ]; then
    ENV_FILE=".env.production"
fi

if [ ! -f "$ENV_EXAMPLE" ] && [ -f .env.production.example ]; then
    ENV_EXAMPLE=".env.production.example"
fi

# Check if .env.production exists
if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        echo "⚠️  No $ENV_FILE file found!"
        echo ""
        echo "Please create $ENV_FILE from $ENV_EXAMPLE:"
        echo "  1. cp $ENV_EXAMPLE $ENV_FILE"
        echo "  2. Edit $ENV_FILE and set:"
        echo "     - POSTGRES_PASSWORD (strong password)"
        echo "     - ORIGIN (your server IP or domain)"
        echo "     - VITE_API_URL (your server IP/domain + /api)"
        echo "     - CORS_ORIGINS (your server IP or domain)"
        echo "     - Optional: OPENROUTER_API_KEY, LOGFIRE_TOKEN"
        echo ""
        exit 1
    else
        echo "❌ Error: No $ENV_EXAMPLE file found!"
        exit 1
    fi
fi

echo "📋 Deployment Configuration:"
echo "   Mode: PRODUCTION (Single-Node Docker Swarm)"
echo "   Compose file: docker-compose.prod.yml"
echo "   Stack Name: jobwizard"
echo ""

# Ask for confirmation
read -p "🔍 Deploy to production stack? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled."
    exit 0
fi

echo ""
echo "📝 Loading environment variables from $ENV_FILE..."
# Export all variables from environment file so docker stack can use them
set -a  # automatically export all variables
source "$ENV_FILE"
set +a  # disable automatic export

echo ""
echo "💾 Running automated pre-flight database backup..."
./scripts/backup-db.sh || echo "⚠️ Pre-flight backup skipped or failed"

echo ""
echo "🐝 Verifying Docker Swarm status..."
SWARM_STATE=$(docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null || echo "inactive")
if [ "$SWARM_STATE" != "active" ]; then
    echo "   Initializing Docker Swarm..."
    docker swarm init --advertise-addr 127.0.0.1 || true
else
    echo "   Docker Swarm is active."
fi

echo ""
# Optional: Ask to wipe database (fresh start)
read -p "⚠️  Wipe database (clear all user data)? (y/N): " wipe_db
echo ""

if [ "$wipe_db" == "y" ] || [ "$wipe_db" == "Y" ]; then
    echo "🧹 Wiping database volume and removing stack..."
    docker stack rm jobwizard 2>/dev/null || true
    docker volume rm jobwizard_postgres_data 2>/dev/null || true
    sleep 5
fi

echo "🧹 Cleaning up any legacy standalone Compose containers..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true

echo ""
echo "🏗️  Building production service images..."
docker compose -f docker-compose.prod.yml build

echo ""
echo "🚀 Deploying stack to Docker Swarm..."
docker stack deploy -c docker-compose.prod.yml jobwizard

echo ""
echo "🌱 Seeding initial data..."
# Wait for backend task container to spin up
sleep 12
BACKEND_CONTAINER=$(docker ps --format '{{.Names}}' | grep "^jobwizard_backend" | head -n 1)

if [ -n "$BACKEND_CONTAINER" ]; then
    docker exec "$BACKEND_CONTAINER" uv run python scripts/seed_user.py || echo "⚠️ Seeding failed or user already exists"
else
    echo "⚠️ Backend container not found yet; seeding can be re-run manually via: docker exec \$(docker ps -q -f name=jobwizard_backend) uv run python scripts/seed_user.py"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Swarm production deployment complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Stack Service Status:"
docker stack services jobwizard

echo ""
echo "🌐 Your application should be accessible at:"
echo "   - Get your server IP with: curl ifconfig.me"
echo "   - Access at: http://YOUR_SERVER_IP"
echo ""
echo "📝 Useful Swarm commands:"
echo "   View stack tasks: docker stack ps jobwizard"
echo "   View service logs: docker service logs -f jobwizard_backend"
echo "   Scale service: docker service scale jobwizard_backend=2"
echo "   Remove stack: docker stack rm jobwizard"
echo ""
