#!/bin/bash

# =====================================================
# WB ANALYTICS INFRASTRUCTURE HEALTH CHECK
# =====================================================

echo "🏥 WB Analytics Infrastructure Health Check"
echo "==========================================="

# Функция проверки сервиса
check_service() {
    local service=$1
    local url=$2
    local expected_response=$3
    
    echo -n "Checking $service... "
    
    if curl -s --max-time 5 "$url" | grep -q "$expected_response" 2>/dev/null; then
        echo "✅ OK"
        return 0
    else
        echo "❌ FAILED"
        return 1
    fi
}

# Функция проверки Docker контейнера
check_container() {
    local container=$1
    echo -n "Checking container $container... "
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container.*Up"; then
        echo "✅ RUNNING"
        return 0
    else
        echo "❌ NOT RUNNING"
        return 1
    fi
}

# Проверяем что Docker запущен
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    exit 1
fi

echo ""
echo "🐳 Docker Containers Status:"
echo "----------------------------"

# Проверяем основные контейнеры
check_container "wb_postgres"
check_container "wb_redis" 
check_container "wb_chromadb"
check_container "wb_minio"
check_container "wb_prometheus"
check_container "wb_grafana"

echo ""
echo "🌐 Service Endpoints Status:"
echo "----------------------------"

# Проверяем эндпоинты сервисов
check_service "PostgreSQL" "http://localhost:5432" "" || {
    # Альтернативная проверка через docker exec
    if docker-compose exec -T postgres pg_isready -U wb_admin -d wb_analytics >/dev/null 2>&1; then
        echo "PostgreSQL connection: ✅ OK"
    else
        echo "PostgreSQL connection: ❌ FAILED"
    fi
}

check_service "Redis" "http://localhost:6379" "" || {
    # Альтернативная проверка через docker exec
    if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        echo "Redis connection: ✅ OK"
    else
        echo "Redis connection: ❌ FAILED"  
    fi
}

check_service "ChromaDB" "http://localhost:8000/api/v1/heartbeat" "OK"
check_service "MinIO" "http://localhost:9000/minio/health/live" "OK"
check_service "Prometheus" "http://localhost:9090/-/healthy" "Prometheus"
check_service "Grafana" "http://localhost:3000/api/health" "ok"
check_service "Adminer" "http://localhost:8080" "Adminer"
check_service "Redis Insight" "http://localhost:8001" ""

echo ""
echo "💾 Database Status:"
echo "-------------------"

# Проверяем подключение к базе и базовые таблицы
if docker-compose exec -T postgres psql -U wb_admin -d wb_analytics -c "SELECT schemaname FROM pg_tables WHERE schemaname IN ('agents', 'tasks', 'compliance') LIMIT 1;" >/dev/null 2>&1; then
    echo "Database schemas: ✅ OK"
    
    # Проверяем количество таблиц
    TABLE_COUNT=$(docker-compose exec -T postgres psql -U wb_admin -d wb_analytics -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema IN ('agents', 'tasks', 'compliance', 'audit', 'metrics');" 2>/dev/null | tr -d ' \n\r')
    echo "Tables count: $TABLE_COUNT ✅"
    
    # Проверяем стандарты соответствия
    STANDARDS_COUNT=$(docker-compose exec -T postgres psql -U wb_admin -d wb_analytics -t -c "SELECT count(*) FROM compliance.standards;" 2>/dev/null | tr -d ' \n\r')
    echo "Compliance standards: $STANDARDS_COUNT ✅"
else
    echo "Database schemas: ❌ FAILED"
fi

echo ""
echo "🔧 System Resources:"
echo "--------------------"

# Проверяем использование ресурсов
if command -v docker stats &> /dev/null; then
    echo "Docker containers resource usage:"
    timeout 3 docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -10
fi

# Проверяем место на диске
echo ""
echo "💽 Disk Space:"
df -h . | tail -1 | awk '{print "Available space: " $4 " (" $5 " used)"}'

echo ""
echo "📊 Quick Stats:"
echo "---------------"
RUNNING_CONTAINERS=$(docker ps -q | wc -l | tr -d ' ')
TOTAL_CONTAINERS=$(docker ps -a -q | wc -l | tr -d ' ')
echo "Containers running: $RUNNING_CONTAINERS/$TOTAL_CONTAINERS"

VOLUMES=$(docker volume ls -q | grep wb-analytics | wc -l | tr -d ' ')
echo "Data volumes: $VOLUMES"

echo ""
echo "🚀 Status Summary:"
echo "------------------"
if [ $RUNNING_CONTAINERS -ge 6 ]; then
    echo "✅ Infrastructure is HEALTHY and ready for development!"
    echo ""
    echo "🔗 Quick Access Links:"
    echo "   📊 Grafana:       http://localhost:3000"
    echo "   🗄️  Database GUI:  http://localhost:8080"  
    echo "   📈 Redis GUI:     http://localhost:8001"
    echo "   💾 MinIO Console: http://localhost:9001"
    exit 0
else
    echo "⚠️  Infrastructure has issues. Some services are not running."
    echo ""
    echo "🔧 Try running:"
    echo "   ./start.sh"
    echo ""
    echo "🔍 For detailed logs:"
    echo "   docker-compose logs -f [service-name]"
    exit 1
fi