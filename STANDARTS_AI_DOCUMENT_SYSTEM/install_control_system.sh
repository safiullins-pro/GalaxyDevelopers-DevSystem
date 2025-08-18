#!/bin/bash
echo " Установка системы автоконтроля разработчиков..."

# Проверка требований
command -v docker >/dev/null 2>&1 || { echo "❌ Docker не установлен"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose не установлен"; exit 1; }

# Создание необходимых директорий
mkdir -p workspace templates

# Запуск системы
echo " Запуск контейнеров..."
docker-compose up -d

# Ожидание запуска БД
echo "⏳ Ожидание запуска PostgreSQL..."
sleep 10

# Настройка Git hooks
echo " Настройка Git hooks..."
mkdir -p .git/hooks
cp git_hooks.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Запуск file monitor
echo "️ Запуск File Monitor..."
python3 file_monitor.py &

echo "✅ Система автоконтроля установлена!"
echo ""
echo " Web Dashboard: http://localhost:8080"
echo " Рабочая директория: ./workspace"
echo ""
echo "Чтобы протестировать систему:"
echo "1. Создайте файл в ./workspace"
echo "2. Добавьте туда password = 'test123'"
echo "3. Попробуйте сделать git commit"
echo "4. Проверьте Web Dashboard"