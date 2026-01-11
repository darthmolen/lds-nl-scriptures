#!/bin/bash
# Backup local PostgreSQL and restore to Azure PostgreSQL
# Usage: ./scripts/db-sync-to-azure.sh

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
LOCAL_HOST="localhost"
LOCAL_PORT="6432"
LOCAL_USER="${POSTGRES_USER:-englishconnect}"
LOCAL_PASSWORD="${POSTGRES_PASSWORD:-devpassword}"
LOCAL_DB="${POSTGRES_DB:-englishconnect}"

AZURE_HOST="psql-ec-4fz3j4ag5rqtu-v4.postgres.database.azure.com"
AZURE_USER="${AZURE_POSTGRES_USER:-ecadmin}"
AZURE_PASSWORD="${AZURE_POSTGRES_PASSWORD}"
AZURE_DB="englishconnect"

BACKUP_FILE="backups/scriptures_$(date +%Y%m%d_%H%M%S).dump"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Database Sync: Local → Azure ===${NC}"
echo ""

# Create backups directory
mkdir -p backups

# Step 1: Dump local database
echo -e "${YELLOW}[1/4] Dumping local database...${NC}"
PGPASSWORD="$LOCAL_PASSWORD" pg_dump \
    -h "$LOCAL_HOST" \
    -p "$LOCAL_PORT" \
    -U "$LOCAL_USER" \
    -Fc \
    "$LOCAL_DB" > "$BACKUP_FILE"

DUMP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo -e "${GREEN}  ✓ Dump complete: $BACKUP_FILE ($DUMP_SIZE)${NC}"

# Step 2: Ensure pgvector extension exists on Azure
echo -e "${YELLOW}[2/4] Ensuring pgvector extension on Azure...${NC}"
PGPASSWORD="$AZURE_PASSWORD" psql \
    -h "$AZURE_HOST" \
    -U "$AZURE_USER" \
    -d "$AZURE_DB" \
    -c "CREATE EXTENSION IF NOT EXISTS vector;" \
    --quiet
echo -e "${GREEN}  ✓ pgvector extension ready${NC}"

# Step 3: Restore to Azure
echo -e "${YELLOW}[3/4] Restoring to Azure PostgreSQL...${NC}"
echo -e "  This may take a few minutes..."
PGPASSWORD="$AZURE_PASSWORD" pg_restore \
    -h "$AZURE_HOST" \
    -U "$AZURE_USER" \
    -d "$AZURE_DB" \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    "$BACKUP_FILE" 2>&1 | grep -v "already exists" || true
echo -e "${GREEN}  ✓ Restore complete${NC}"

# Step 4: Verify counts on Azure
echo -e "${YELLOW}[4/4] Verifying data on Azure...${NC}"
VERSE_COUNT=$(PGPASSWORD="$AZURE_PASSWORD" psql \
    -h "$AZURE_HOST" \
    -U "$AZURE_USER" \
    -d "$AZURE_DB" \
    -t \
    -c "SELECT COUNT(*) FROM scriptures WHERE embedding IS NOT NULL;")
VERSE_COUNT=$(echo "$VERSE_COUNT" | xargs)

CFM_COUNT=$(PGPASSWORD="$AZURE_PASSWORD" psql \
    -h "$AZURE_HOST" \
    -U "$AZURE_USER" \
    -d "$AZURE_DB" \
    -t \
    -c "SELECT COUNT(*) FROM cfm_lessons;")
CFM_COUNT=$(echo "$CFM_COUNT" | xargs)

echo -e "${GREEN}  ✓ Verses with embeddings: $VERSE_COUNT${NC}"
echo -e "${GREEN}  ✓ CFM lessons: $CFM_COUNT${NC}"

echo ""
echo -e "${GREEN}=== Sync Complete ===${NC}"
echo "Backup saved to: $BACKUP_FILE"
