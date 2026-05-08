#!/usr/bin/env bash
# Script to start Job Wizard locally for development
# Use this on your laptop/workstation, NOT on the production server

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Starting Job Wizard - LOCAL DEVELOPMENT MODE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "   Please start Docker Desktop and try again."
    exit 1
fi

# Check if .env exists, if not use .env.example
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        echo "⚠️  No .env file found at $ENV_FILE. Creating from $ENV_EXAMPLE..."
        # Create .env from example
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo "✅ Created $ENV_FILE"
        echo ""
        echo "📝 NOTE: Edit $ENV_FILE and set your API keys if needed:"
        echo "   - OPENROUTER_API_KEY (optional, for remote LLM)"
        echo "   - LOGFIRE_TOKEN (optional, for observability)"
        echo ""
    else
        echo "❌ Error: No $ENV_EXAMPLE file found!"
        exit 1
    fi
fi

# Ensure we're using localhost URLs for local development
export VITE_API_URL="http://localhost:8000"
export CORS_ORIGINS="http://localhost:3000,http://localhost:5173"

echo "📋 Configuration:"
echo "   API URL: $VITE_API_URL"
echo "   CORS: $CORS_ORIGINS"
echo ""

# Start services
echo "🐳 Starting Docker containers..."
echo ""

# Use docker-compose if available, else docker compose
if command -v docker-compose > /dev/null 2>&1; then
    docker-compose up --build -d
    echo "Logs:"
    docker-compose logs -f backend frontend
else
    docker compose up --build -d
    echo "Logs:"
    docker compose logs -f backend frontend
fi
