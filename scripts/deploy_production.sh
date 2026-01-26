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

# Check if .env.production exists
if [ ! -f .env.production ]; then
    if [ -f .env.production.example ]; then
        echo "⚠️  No .env.production file found!"
        echo ""
        echo "Please create .env.production from .env.production.example:"
        echo "  1. cp .env.production.example .env.production"
        echo "  2. Edit .env.production and set:"
        echo "     - POSTGRES_PASSWORD (strong password)"
        echo "     - ORIGIN (your server IP or domain)"
        echo "     - VITE_API_URL (your server IP/domain + /api)"
        echo "     - CORS_ORIGINS (your server IP or domain)"
        echo "     - Optional: OPENROUTER_API_KEY, LOGFIRE_TOKEN"
        echo ""
        exit 1
    else
        echo "❌ Error: No .env.production.example file found!"
        exit 1
    fi
fi

echo "📋 Deployment Configuration:"
echo "   Mode: PRODUCTION"
echo "   Compose file: docker-compose.prod.yml"
echo ""

# Ask for confirmation
read -p "🔍 Deploy to production? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled."
    exit 0
fi

echo ""
echo "📝 Loading environment variables from .env.production..."
# Export all variables from .env.production so docker-compose can use them
set -a  # automatically export all variables
source .env.production
set +a  # disable automatic export

echo ""
# Optional: Ask to wipe database (fresh start)
read -p "⚠️  Wipe database (clear all user data)? (y/N): " wipe_db
echo ""
echo "🐳 Stopping any existing containers..."

if [ "$wipe_db" == "y" ] || [ "$wipe_db" == "Y" ]; then
    echo "🧹 Wiping database volume..."
    docker compose -f docker-compose.prod.yml down -v
else
    docker compose -f docker-compose.prod.yml down
fi

echo ""
echo "🏗️  Building and starting production services..."
echo ""

# Use docker-compose if available, else docker compose
if command -v docker-compose > /dev/null 2>&1; then
    docker-compose -f docker-compose.prod.yml up -d --build
else
    docker compose -f docker-compose.prod.yml up -d --build
fi

echo ""
echo "🌱 Seeding initial data..."
# Wait for backend to be ready (naive sleep)
sleep 10
if command -v docker-compose > /dev/null 2>&1; then
    docker-compose -f docker-compose.prod.yml exec -T backend python seed_user.py || echo "⚠️ Seeding failed or user already exists"
else
    # Try to copy script just in case getting 502/not found
    docker cp backend/seed_user.py jobwizard-backend-prod:/app/seed_user.py >/dev/null 2>&1 || true
    docker compose -f docker-compose.prod.yml exec -T backend python seed_user.py || echo "⚠️ Seeding failed or user already exists"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Production deployment complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Service Status:"
if command -v docker-compose > /dev/null 2>&1; then
    docker-compose -f docker-compose.prod.yml ps
else
    docker compose -f docker-compose.prod.yml ps
fi

echo ""
echo "🌐 Your application should be accessible at:"
echo "   - Get your server IP with: curl ifconfig.me"
echo "   - Access at: http://YOUR_SERVER_IP"
echo ""
echo "📝 Useful commands:"
echo "   View logs: docker compose -f docker-compose.prod.yml logs -f"
echo "   Stop services: docker compose -f docker-compose.prod.yml down"
echo "   Restart: docker compose -f docker-compose.prod.yml restart"
echo ""
