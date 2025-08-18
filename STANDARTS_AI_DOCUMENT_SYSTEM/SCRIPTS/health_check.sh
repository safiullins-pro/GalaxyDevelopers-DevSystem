#!/usr/bin/env bash
# Проверка здоровья системы GalaxyDevelopment

set -e

echo "🏥 Проверка здоровья системы GalaxyDevelopment..."
echo ""

# Функция для проверки HTTP эндпоинта
check_endpoint() {
    local url=$1
    local name=$2
    local timeout=${3:-5}
    
    if curl -s --connect-timeout $timeout "$url" > /dev/null 2>&1; then
        echo "✅ $name: OK"
        return 0
    else
        echo "❌ $name: НЕДОСТУПЕН"
        return 1
    fi
}

# Функция для проверки контейнера
check_container() {
    local container_name=$1
    local status=$(docker-compose ps -q $container_name | xargs docker inspect --format='{{.State.Status}}' 2>/dev/null)
    
    if [ "$status" = "running" ]; then
        echo "✅ $container_name: ЗАПУЩЕН"
        return 0
    else
        echo "❌ $container_name: НЕ ЗАПУЩЕН ($status)"
        return 1
    fi
}

# Проверка инфраструктуры
echo "🔧 Инфраструктура:"
check_container "zookeeper"
check_container "kafka" 
check_container "postgres"
check_container "redis"

echo ""

# Проверка AI-агентов
echo "🤖 AI-агенты:"
check_container "research-agent"
check_container "composer-agent"
check_container "reviewer-agent"
check_container "integrator-agent"
check_container "publisher-agent"

echo ""

# Проверка мониторинга
echo "📈 Мониторинг:"
check_container "prometheus"
check_container "grafana"

echo ""

# Проверка HTTP эндпоинтов
echo "🌐 HTTP сервисы:"
check_endpoint "http://localhost:3000" "Grafana Dashboard"
check_endpoint "http://localhost:9090" "Prometheus"
check_endpoint "http://localhost:8000/metrics" "ResearchAgent metrics"
check_endpoint "http://localhost:8001/metrics" "ComposerAgent metrics"

echo ""

# Проверка базы данных
echo "🗄️ База данных:"
if docker-compose exec -T postgres pg_isready -U galaxy -d galaxydevelopment > /dev/null 2>&1; then
    echo "✅ PostgreSQL: OK"
    
    # Проверка таблиц
    table_count=$(docker-compose exec -T postgres psql -U galaxy -d galaxydevelopment -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
    echo "  📊 Таблиц в БД: $table_count"
    
    # Проверка агентов в БД
    agent_count=$(docker-compose exec -T postgres psql -U galaxy -d galaxydevelopment -t -c "SELECT COUNT(*) FROM agents WHERE status = 'active';" | tr -d ' ' 2>/dev/null || echo "0")
    echo "  🤖 Активных агентов: $agent_count"
else
    echo "❌ PostgreSQL: НЕДОСТУПЕН"
fi

echo ""

# Проверка Kafka топиков
echo "📨 Kafka топики:"
if docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; then
    topics=$(docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list | grep -E "(research|composer|reviewer|integrator|publisher|status)" | wc -l)
    echo "✅ Kafka: OK ($topics топиков)"
else
    echo "❌ Kafka: НЕДОСТУПЕН"
fi

echo ""

# Проверка логов агентов
echo "📝 Логи агентов:"
log_files=("research_agent.log" "composer_agent.log")
for log_file in "${log_files[@]}"; do
    if [ -f "logs/$log_file" ]; then
        size=$(du -h "logs/$log_file" | cut -f1)
        echo "  📄 $log_file: $size"
    else
        echo "  📄 $log_file: не найден"
    fi
done

echo ""

# Проверка использования ресурсов
echo "💻 Использование ресурсов:"
echo "  🔷 Docker контейнеры:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -10

echo ""

# Общий статус
failed_checks=0

# Подсчет неудачных проверок
for container in "zookeeper" "kafka" "postgres" "redis" "research-agent" "composer-agent" "prometheus" "grafana"; do
    if ! docker-compose ps -q $container | xargs docker inspect --format='{{.State.Status}}' 2>/dev/null | grep -q "running"; then
        ((failed_checks++))
    fi
done

echo "📋 СВОДКА:"
total_checks=8
successful_checks=$((total_checks - failed_checks))
echo "  ✅ Успешных проверок: $successful_checks/$total_checks"
echo "  ❌ Неудачных проверок: $failed_checks/$total_checks"

if [ $failed_checks -eq 0 ]; then
    echo "  🟢 Статус системы: ЗДОРОВА"
    exit 0
elif [ $failed_checks -le 2 ]; then
    echo "  🟡 Статус системы: ЧАСТИЧНО РАБОТАЕТ"
    exit 1
else
    echo "  🔴 Статус системы: КРИТИЧЕСКИЕ ПРОБЛЕМЫ"
    exit 2
fi