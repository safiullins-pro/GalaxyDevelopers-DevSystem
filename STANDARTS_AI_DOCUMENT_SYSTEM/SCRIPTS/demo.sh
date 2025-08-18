#!/usr/bin/env bash
# Демонстрация системы GalaxyDevelopment

set -e

echo "🌌 ДЕМОНСТРАЦИЯ СИСТЕМЫ GALAXYDEVELOPMENT"
echo "========================================="
echo ""

echo "🎯 Эта демонстрация покажет:"
echo "  • Запуск всей инфраструктуры"
echo "  • Создание 150+ IT-процессов"
echo "  • Работу AI-агентов"
echo "  • Генерацию документации"
echo "  • Мониторинг системы"
echo ""

read -p "Нажмите Enter для начала демонстрации..."
echo ""

# Шаг 1: Проверка окружения
echo "🔧 Шаг 1: Проверка окружения"
echo "-----------------------------"

if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Установите Docker Desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose не найден"  
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден"
    exit 1
fi

echo "✅ Docker: установлен"
echo "✅ docker-compose: установлен" 
echo "✅ Python3: установлен"
echo ""

# Шаг 2: Запуск системы
echo "🚀 Шаг 2: Запуск системы GalaxyDevelopment"
echo "-------------------------------------------"
echo "Запускаем всю инфраструктуру..."
echo ""

./scripts/start_agents.sh

echo ""
read -p "Нажмите Enter когда система запустится..."
echo ""

# Шаг 3: Проверка здоровья
echo "🏥 Шаг 3: Проверка здоровья системы"
echo "-----------------------------------"

./scripts/health_check.sh

echo ""
read -p "Нажмите Enter для продолжения..."
echo ""

# Шаг 4: Генерация процессов
echo "🏭 Шаг 4: Генерация 150+ IT-процессов"
echo "------------------------------------"
echo "Создаем задачи для автоматической генерации документации..."
echo ""

# Установка зависимостей для скрипта
pip3 install kafka-python > /dev/null 2>&1

# Запуск генерации (автоматически отвечаем 'y')
echo "y" | python3 scripts/generate_processes.py

echo ""
echo "📊 Задачи отправлены! AI-агенты начали работу..."
echo ""

# Шаг 5: Мониторинг прогресса
echo "📈 Шаг 5: Мониторинг прогресса"
echo "------------------------------"
echo "Следите за работой агентов в реальном времени:"
echo ""
echo "🌐 Откройте в браузере:"
echo "  • Grafana: http://localhost:3000 (admin/galaxy2025)"
echo "  • Prometheus: http://localhost:9090"
echo ""

echo "📊 Метрики агентов:"
echo "  • ResearchAgent: http://localhost:8000/metrics"
echo "  • ComposerAgent: http://localhost:8001/metrics"
echo ""

echo "💾 Логи агентов:"
docker-compose logs --tail=20 research-agent
echo ""
docker-compose logs --tail=20 composer-agent

echo ""
read -p "Нажмите Enter для просмотра прогресса в БД..."
echo ""

# Шаг 6: Просмотр результатов в БД
echo "🗄️ Шаг 6: Просмотр результатов"
echo "------------------------------"

echo "Количество обработанных процессов:"
docker-compose exec -T postgres psql -U galaxy -d galaxydevelopment -c "
SELECT 
    COUNT(*) as total_processes,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
FROM agent_tasks;
"

echo ""
echo "Статус агентов:"
docker-compose exec -T postgres psql -U galaxy -d galaxydevelopment -c "
SELECT agent_name, status, processed_count, error_count, last_ping
FROM agents 
ORDER BY agent_name;
"

echo ""
echo "Сгенерированная документация:"
docker-compose exec -T postgres psql -U galaxy -d galaxydevelopment -c "
SELECT process_id, doc_type, quality_score, created_at
FROM documentation 
ORDER BY created_at DESC 
LIMIT 10;
"

echo ""

# Шаг 7: Демонстрация результатов
echo "📝 Шаг 7: Пример сгенерированной документации"
echo "---------------------------------------------"

# Получаем пример документа из БД
echo "Получаем пример документации для процесса Incident Management:"
echo ""

docker-compose exec -T postgres psql -U galaxy -d galaxydevelopment -c "
SELECT content 
FROM documentation 
WHERE process_id = '001' AND doc_type = 'composed'
LIMIT 1;
" | head -50

echo ""
echo "... (документ обрезан для демонстрации) ..."
echo ""

# Финальная статистика
echo "📊 ФИНАЛЬНАЯ СТАТИСТИКА ДЕМОНСТРАЦИИ"
echo "===================================="

echo "🎯 Что продемонстрировано:"
echo "  ✅ Запуск полной инфраструктуры (Kafka, PostgreSQL, Redis)"
echo "  ✅ Работа 5 AI-агентов в режиме реального времени"
echo "  ✅ Обработка каталога из 150+ IT-процессов"
echo "  ✅ Автоматическая генерация документации по стандартам ITIL/ISO"
echo "  ✅ Система мониторинга и метрик"
echo "  ✅ Масштабируемая архитектура на Docker"
echo ""

echo "🔮 Возможности системы:"
echo "  • Поддержка стандартов: ITIL 4, ISO/IEC 20000, COBIT, NIST, ISO 27001"
echo "  • AI-улучшение документации через OpenAI GPT-4"
echo "  • Интеграция с Git, Confluence, SharePoint"
echo "  • Автоматические чек-листы и процедуры"
echo "  • Метрики качества и соответствия стандартам"
echo "  • Команда из 35 специализированных ролей"
echo ""

echo "💻 Система продолжает работать в фоне!"
echo "📈 Следите за прогрессом: http://localhost:3000"
echo "🛑 Для остановки: ./scripts/stop_agents.sh"
echo ""

echo "🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!"
echo "Система GalaxyDevelopment готова к production использованию!"