#!/bin/bash

# Quick start script for development

set -e

echo "🚀 Cyper Security Agent - Quick Start"
echo "====================================="
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required but not installed"
    exit 1
fi

# Create .env if doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Edit .env and set your ANTHROPIC_API_KEY"
    echo ""
    read -p "Press Enter to continue (or Ctrl+C to abort and edit .env first)..."
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if gateway is responding
echo "🔍 Checking gateway health..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ Gateway is healthy"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Gateway failed to start"
    echo "Check logs with: docker-compose logs -f gateway"
    exit 1
fi

echo ""
echo "🎉 Cyper Security Agent is running!"
echo ""
echo "📍 Services:"
echo "   - API Gateway: http://localhost:8080"
echo "   - Dashboard:   http://localhost:3000"
echo "   - PostgreSQL:  localhost:5432"
echo "   - Redis:       localhost:6379"
echo ""
echo "🔑 Default Admin:"
echo "   Email:    admin@cyper.security"
echo "   Password: Admin123!"
echo ""
echo "📚 Next Steps:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Run tests: ./scripts/test.sh"
echo "   3. View logs: docker-compose logs -f"
echo ""
echo "🛑 To stop: docker-compose down"
echo ""
