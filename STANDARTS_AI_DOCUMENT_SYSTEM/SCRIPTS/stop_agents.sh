#!/usr/bin/env bash
# Остановка всех сервисов системы GalaxyDevelopment

echo "🛑 Остановка системы GalaxyDevelopment..."

# Остановка и удаление контейнеров
docker-compose down

# Очистка неиспользуемых ресурсов
docker system prune -f

echo "✅ Система остановлена"