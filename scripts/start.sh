#!/bin/bash
# Quick start script for Docker deployment

set -e

echo "🚀 Starting RAG System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.production..."
    cp .env.production .env
    echo "📝 Please edit .env with your OpenAI API key before continuing."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🐳 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check health
HEALTH=$(curl -s http://localhost:8000/health || echo "failed")

if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ System is running!"
    echo ""
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo "🔍 Health Check: http://localhost:8000/health"
    echo ""
    echo "To view logs: docker-compose logs -f"
    echo "To stop: docker-compose down"
else
    echo "❌ System failed to start. Check logs with: docker-compose logs"
    exit 1
fi
