#!/usr/bin/env bash
# Скрипт запуска всех агентов системы GalaxyDevelopment

set -e

echo "🌌 Запуск системы GalaxyDevelopment..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Установите Docker и повторите попытку."
    exit 1
fi

# Проверка docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose не найден. Установите docker-compose и повторите попытку."
    exit 1
fi

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p logs
mkdir -p data/kafka
mkdir -p data/postgres
mkdir -p data/grafana

# Запуск инфраструктуры
echo "🚀 Запуск инфраструктуры (Kafka, PostgreSQL, Redis)..."
docker-compose up -d zookeeper kafka postgres redis

# Ожидание готовности инфраструктуры
echo "⏳ Ожидание готовности инфраструктуры..."
sleep 30

# Создание топиков Kafka
echo "📨 Создание топиков Kafka..."
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic research_tasks --partitions 3 --replication-factor 1 || true
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic composer_tasks --partitions 3 --replication-factor 1 || true
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic reviewer_tasks --partitions 3 --replication-factor 1 || true
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic integrator_tasks --partitions 3 --replication-factor 1 || true
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic publisher_tasks --partitions 3 --replication-factor 1 || true
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic agent_status_updates --partitions 1 --replication-factor 1 || true
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic system_logs --partitions 1 --replication-factor 1 || true

# Инициализация базы данных
echo "🗄️ Инициализация базы данных..."
sleep 10  # Дополнительное время для готовности PostgreSQL

# Запуск агентов
echo "🤖 Запуск AI-агентов..."

echo "  📊 Запуск ResearchAgent..."
docker-compose up -d research-agent

sleep 5

echo "  ✍️ Запуск ComposerAgent..."  
docker-compose up -d composer-agent

sleep 5

echo "  🔍 Запуск ReviewerAgent..."
docker-compose up -d reviewer-agent

sleep 5

echo "  🔗 Запуск IntegratorAgent..."
docker-compose up -d integrator-agent

sleep 5

echo "  📤 Запуск PublisherAgent..."
docker-compose up -d publisher-agent

# Запуск мониторинга
echo "📈 Запуск мониторинга (Prometheus + Grafana)..."
docker-compose up -d prometheus grafana

# Проверка статуса всех сервисов
echo "🔍 Проверка статуса сервисов..."
docker-compose ps

# Информация о доступе
echo ""
echo "✅ Система GalaxyDevelopment запущена!"
echo ""
echo "🌐 Доступные интерфейсы:"
echo "  • Grafana Dashboard: http://localhost:3000 (admin/galaxy2025)"
echo "  • Prometheus: http://localhost:9090"
echo "  • ResearchAgent metrics: http://localhost:8000/metrics"
echo "  • ComposerAgent metrics: http://localhost:8001/metrics"
echo ""
echo "📊 Топики Kafka:"
echo "  • research_tasks - задачи для исследования"
echo "  • composer_tasks - задачи для генерации документации"
echo "  • reviewer_tasks - задачи для валидации"
echo "  • integrator_tasks - задачи для интеграции"  
echo "  • publisher_tasks - задачи для публикации"
echo "  • agent_status_updates - статусы агентов"
echo ""
echo "🗄️ База данных PostgreSQL:"
echo "  • Host: localhost:5432"
echo "  • Database: galaxydevelopment"
echo "  • User: galaxy"
echo ""
echo "📝 Логи агентов доступны в директории: logs/"
echo ""
echo "Используйте './scripts/health_check.sh' для проверки здоровья системы"
echo "Используйте './scripts/stop_agents.sh' для остановки всех сервисов"