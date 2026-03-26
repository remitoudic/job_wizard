#!/usr/bin/env bash
# Script to backup the PostgreSQL database
# Creates timestamped backup in backups/ directory

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💾 Database Backup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create backups directory if it doesn't exist
BACKUP_DIR="services/backups"
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/jobwizard_${TIMESTAMP}.sql"

# Get database credentials from .env
if [ -f .env/.env ]; then
    source .env/.env
fi

# Use defaults if not set
POSTGRES_USER=${POSTGRES_USER:-jobwizard}
POSTGRES_DB=${POSTGRES_DB:-jobwizard}

echo "📦 Creating backup..."
echo "   Database: $POSTGRES_DB"
echo "   File: $BACKUP_FILE"
echo ""

# Determine container name (check both prod and dev)
if docker ps --format '{{.Names}}' | grep -q "^jobwizard-postgres-prod$"; then
    CONTAINER_NAME="jobwizard-postgres-prod"
elif docker ps --format '{{.Names}}' | grep -q "^jobwizard-postgres$"; then
    CONTAINER_NAME="jobwizard-postgres"
else
    echo "⚠️  No running database container found, skipping backup."
    exit 0
fi

echo "   Container: $CONTAINER_NAME"

# Create backup using docker exec
docker exec "$CONTAINER_NAME" pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    > "$BACKUP_FILE"

# Check if backup was successful
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup successful!"
    echo "   Size: $BACKUP_SIZE"
    echo "   Location: $BACKUP_FILE"
    
    # Keep only last 10 backups
    echo ""
    echo "🧹 Cleaning old backups (keeping last 10)..."
    ls -t "${BACKUP_DIR}"/jobwizard_*.sql | tail -n +11 | xargs -r rm
    
    BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}"/jobwizard_*.sql 2>/dev/null | wc -l)
    echo "   Current backups: $BACKUP_COUNT"
else
    echo "❌ Backup failed!"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
