#!/bin/bash

# Database initialization script

set -e

echo "🗄️  Initializing Cyper Security Database"
echo "========================================"
echo ""

# Check if PostgreSQL is running
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL client (psql) not found"
    echo "   Please install PostgreSQL or run via Docker"
    exit 1
fi

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-cyper_security}"
DB_USER="${DB_USER:-cyper_admin}"
DB_PASSWORD="${DB_PASSWORD:-changeme}"

export PGPASSWORD="$DB_PASSWORD"

echo "📋 Database Configuration:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo ""

# Test connection
echo "🔌 Testing database connection..."
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c '\q' 2>/dev/null; then
    echo "✅ Connected to PostgreSQL"
else
    echo "❌ Failed to connect to PostgreSQL"
    echo "   Make sure PostgreSQL is running and credentials are correct"
    exit 1
fi
echo ""

# Create database if it doesn't exist
echo "🏗️  Creating database..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME"
echo "✅ Database ready: $DB_NAME"
echo ""

# Apply schema
echo "📝 Applying schema..."
if [ -f "database/schema.sql" ]; then
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database/schema.sql
    echo "✅ Schema applied successfully"
else
    echo "❌ Schema file not found: database/schema.sql"
    exit 1
fi
echo ""

# Verify tables
echo "🔍 Verifying tables..."
table_count=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
echo "✅ Created $table_count tables"
echo ""

# Show admin credentials
echo "🔑 Default Admin Credentials:"
echo "   Email: admin@cyper.security"
echo "   Password: Admin123!"
echo "   ⚠️  CHANGE THESE IN PRODUCTION!"
echo ""

echo "🎉 Database initialization complete!"
echo ""
