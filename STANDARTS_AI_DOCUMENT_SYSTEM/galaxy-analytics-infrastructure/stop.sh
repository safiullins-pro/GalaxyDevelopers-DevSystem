#!/bin/bash

# =====================================================
# WB ANALYTICS INFRASTRUCTURE STOP SCRIPT
# =====================================================

echo "🛑 Stopping WB Analytics Infrastructure..."

# Останавливаем все контейнеры
docker-compose down

if [ "$1" = "--clean" ]; then
    echo "🧹 Removing all data (volumes)..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    echo "🗑️  All data removed!"
else
    echo "💾 Data volumes preserved. Use --clean to remove all data."
fi

echo "✅ WB Analytics Infrastructure stopped!"