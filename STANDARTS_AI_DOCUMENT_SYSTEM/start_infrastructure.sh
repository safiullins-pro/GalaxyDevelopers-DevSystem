#!/bin/bash

# Start Infrastructure Script for DocumentsSystem
# This script launches the minimal required infrastructure

set -e  # Exit on error

echo "🚀 Starting DocumentsSystem Infrastructure..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p logs

# Copy production env if not exists
if [ ! -f .env ]; then
    echo "📝 Setting up production environment..."
    cp .env.production .env
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.minimal.yml down 2>/dev/null || true

# Start PostgreSQL and Redis
echo "🐘 Starting PostgreSQL..."
echo "🔴 Starting Redis..."
docker-compose -f docker-compose.minimal.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check PostgreSQL
until docker exec galaxy_postgres pg_isready -U galaxy_user -d documents_system > /dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Check Redis
until docker exec galaxy_redis redis-cli -a "redis2025" ping > /dev/null 2>&1; do
    echo "   Waiting for Redis..."
    sleep 2
done
echo "✅ Redis is ready"

# Run database migrations
echo "🔄 Running database migrations..."
if [ -f data/02_DATA/database/database_schema.sql ]; then
    docker exec -i galaxy_postgres psql -U galaxy_user -d documents_system < data/02_DATA/database/database_schema.sql 2>/dev/null || echo "   Schema already exists"
fi

# Create research_results table if not exists
echo "📊 Creating research_results table..."
docker exec galaxy_postgres psql -U galaxy_user -d documents_system -c "
CREATE TABLE IF NOT EXISTS research_results (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(255),
    query TEXT,
    results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);" 2>/dev/null || true

# Show status
echo ""
echo "✅ Infrastructure is ready!"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.minimal.yml ps

echo ""
echo "🔗 Connection Details:"
echo "   PostgreSQL: localhost:5432 (user: galaxy_user, db: documents_system)"
echo "   Redis: localhost:6379"
echo ""
echo "📝 Logs available at: ./logs/"
echo ""
echo "🛑 To stop: ./stop_infrastructure.sh"
echo ""
echo "🎉 Infrastructure started successfully!"