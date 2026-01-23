#!/usr/bin/env bash
# Script to start Job Wizard on production server (147.93.111.113)
# Use this ONLY on the production server, NOT on your laptop

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Starting Job Wizard - PRODUCTION MODE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    exit 1
fi

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

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: No .env file found!"
    echo "   Production requires a configured .env file."
    exit 1
fi

# Set production URLs
export VITE_API_URL="http://${EXPECTED_IP}:8000"
export CORS_ORIGINS="http://localhost:3000,http://localhost:5173,http://${EXPECTED_IP}:5173,http://${EXPECTED_IP}:3000"

echo "📋 Production Configuration:"
echo "   Server IP: $EXPECTED_IP"
echo "   API URL: $VITE_API_URL"
echo ""

# Start services
echo "🐳 Starting Docker containers in production mode..."
echo ""

# Use docker-compose if available, else docker compose
if command -v docker-compose > /dev/null 2>&1; then
    docker-compose up -d --build
else
    docker compose up -d --build
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Services started in background (detached mode)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Access your application at:"
echo "   Frontend: http://${EXPECTED_IP}:5173"
echo "   Backend:  http://${EXPECTED_IP}:8000"
echo "   API Docs: http://${EXPECTED_IP}:8000/docs"
echo ""
echo "📊 Monitor services:"
echo "   docker ps                    # Check running containers"
echo "   docker compose logs -f       # Follow logs"
echo "   docker compose logs backend  # View backend logs"
echo ""
