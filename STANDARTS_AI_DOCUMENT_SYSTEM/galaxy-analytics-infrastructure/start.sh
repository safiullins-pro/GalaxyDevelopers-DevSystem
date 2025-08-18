#!/bin/bash

# =====================================================
# WB ANALYTICS INFRASTRUCTURE STARTUP SCRIPT
# =====================================================

set -e

echo "🚀 Starting WB Analytics Infrastructure..."

# Проверяем что Docker запущен
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker не запущен. Запустите Docker Desktop и попробуйте снова."
    exit 1
fi

# Проверяем что есть .env файл
if [ ! -f .env ]; then
    echo "📄 Создаем .env файл из примера..."
    cp .env.example .env
    echo "⚠️  Отредактируйте .env файл при необходимости"
fi

# Создаем необходимые директории
echo "📁 Создаем директории..."
mkdir -p logs/{postgres,redis,grafana,prometheus}
mkdir -p data/{postgres,redis,grafana,prometheus,minio}

# Проверяем свободное место (нужно минимум 10GB)
AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
if [ $AVAILABLE_SPACE -lt 10485760 ]; then
    echo "⚠️  Мало места на диске. Рекомендуется минимум 10GB свободного места."
fi

# Останавливаем существующие контейнеры если есть
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose down --remove-orphans 2>/dev/null || true

# Удаляем старые volumes если нужно
if [ "$1" = "--clean" ]; then
    echo "🧹 Удаляем старые данные..."
    docker-compose down -v --remove-orphans
    docker system prune -f
fi

# Загружаем образы
echo "📦 Загружаем Docker образы..."
docker-compose pull

# Запускаем базовые сервисы
echo "🔧 Запускаем базовые сервисы..."
docker-compose up -d postgres redis chromadb minio

# Ждем пока PostgreSQL будет готов
echo "⏳ Ждем готовности PostgreSQL..."
timeout 60 bash -c 'until docker-compose exec -T postgres pg_isready -U wb_admin -d wb_analytics; do sleep 2; done'

# Ждем пока Redis будет готов  
echo "⏳ Ждем готовности Redis..."
timeout 30 bash -c 'until docker-compose exec -T redis redis-cli --raw incr ping > /dev/null 2>&1; do sleep 2; done'

# Запускаем мониторинг
echo "📊 Запускаем мониторинг..."
docker-compose up -d prometheus grafana loki promtail

# Запускаем вспомогательные сервисы
echo "🛠  Запускаем вспомогательные сервисы..."
docker-compose up -d adminer redis-insight

# Ждем пока Grafana будет готов
echo "⏳ Ждем готовности Grafana..."
timeout 60 bash -c 'until curl -s http://localhost:3000/api/health > /dev/null 2>&1; do sleep 2; done'

# Проверяем статус всех сервисов
echo "🔍 Проверяем статус сервисов..."
docker-compose ps

echo ""
echo "✅ WB Analytics Infrastructure запущена!"
echo ""
echo "🔗 Доступные сервисы:"
echo "   📊 Grafana:        http://localhost:3000 (admin/wb_grafana_2024)"
echo "   🔍 Prometheus:     http://localhost:9090"
echo "   🗄️  Adminer:        http://localhost:8080 (postgres, wb_admin, wb_secure_pass_2024)"
echo "   📈 Redis Insight:  http://localhost:8001"
echo "   💾 MinIO Console:  http://localhost:9001 (wb_minio_admin/wb_minio_secure_2024)"
echo "   🔌 ChromaDB:       http://localhost:8000"
echo ""
echo "🏥 Health checks:"
echo "   PostgreSQL: $(docker-compose exec -T postgres pg_isready -U wb_admin -d wb_analytics 2>/dev/null && echo '✅ Ready' || echo '❌ Not Ready')"
echo "   Redis:      $(docker-compose exec -T redis redis-cli ping 2>/dev/null && echo '✅ Ready' || echo '❌ Not Ready')"
echo "   ChromaDB:   $(curl -s http://localhost:8000/api/v1/heartbeat 2>/dev/null && echo '✅ Ready' || echo '❌ Not Ready')"
echo ""
echo "🚀 Инфраструктура готова для разработки!"
echo ""
echo "Следующие шаги:"
echo "1. Запустите агентов: npm run start:agents"  
echo "2. Откройте Grafana для мониторинга"
echo "3. Проверьте подключение к БД через Adminer"
echo ""