#!/bin/bash

# Cyper Security Agent - Setup Script

set -e

echo "🔐 Cyper Security Agent - Setup"
echo "================================"
echo ""

# Check for required tools
echo "Checking prerequisites..."

command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Aborting." >&2; exit 1; }

echo "✅ Docker and Docker Compose found"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and set your API keys and passwords"
    echo ""
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p scans reports logs/{core,gateway,brain,nginx,celery} audit_logs database/migrations

echo "✅ Directories created"
echo ""

# Display Terms of Use
echo "📜 TERMS OF USE"
echo "==============="
echo ""
echo "⚠️  WARNING: You must read and accept the Terms of Use before proceeding."
echo ""
echo "Please read TERMS_OF_USE.md and RESPONSIBLE_USE.md"
echo ""
read -p "Have you read and understand the Terms of Use? (yes/no): " terms_acceptance

if [ "$terms_acceptance" != "yes" ]; then
    echo "❌ You must accept the Terms of Use to continue."
    exit 1
fi

echo ""
read -p "Type 'I ACCEPT' to confirm: " final_confirmation

if [ "$final_confirmation" != "I ACCEPT" ]; then
    echo "❌ Setup cancelled."
    exit 1
fi

echo ""
echo "✅ Terms accepted"
echo ""

# Log acceptance
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - Terms of Use v1.0 accepted" >> .terms_acceptance.log

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and set your configuration"
echo "2. Run 'docker-compose up -d' to start all services"
echo "3. Access the dashboard at http://localhost:3000"
echo ""
echo "For development:"
echo "- Rust core: cd core && cargo build"
echo "- Go gateway: cd gateway && go run cmd/server/main.go"
echo "- Python brain: cd brain && pip install -e ."
echo "- Dashboard: cd dashboard && npm install && npm run dev"
echo ""
