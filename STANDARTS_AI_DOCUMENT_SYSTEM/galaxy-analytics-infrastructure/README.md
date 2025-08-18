# 🚀 Galaxy Analytics Infrastructure

Полная инфраструктура для системы аналитики Wildberries с агентами, мониторингом и compliance контролем.

## ⚡ Быстрый старт

```bash
# 1. Настройка окружения
make dev-setup

# 2. Запуск всех сервисов  
make start

# 3. Проверка состояния
make health

# 4. Открыть Grafana
make grafana
```

## 🏗️ Архитектура

### Основные компоненты:
- **PostgreSQL 15** - основная база данных с полной схемой
- **Redis 7** - message bus и кэширование
- **ChromaDB** - векторная база для памяти агентов  
- **MinIO** - S3-совместимое хранилище файлов

### Мониторинг:
- **Prometheus** - сбор метрик
- **Grafana** - визуализация и дашборды
- **Loki + Promtail** - централизованное логирование

### Очереди сообщений:
- **RabbitMQ** - надежная очередь сообщений
- **Kafka + Zookeeper** - высоконагруженные потоки

### Инструменты разработки:
- **Adminer** - веб-интерфейс для PostgreSQL
- **Redis Insight** - GUI для Redis

## 📊 Доступные сервисы

| Сервис | URL | Логин | Пароль |
|--------|-----|-------|--------|
| Grafana | http://localhost:3000 | admin | galaxy_grafana_2024 |
| Adminer | http://localhost:8080 | galaxy_admin | galaxy_secure_pass_2024 |
| Redis Insight | http://localhost:8001 | - | galaxy_redis_secure_2024 |
| MinIO Console | http://localhost:9001 | galaxy_minio_admin | galaxy_minio_secure_2024 |
| Prometheus | http://localhost:9090 | - | - |
| ChromaDB | http://localhost:8000 | - | galaxy_chroma_token_2024 |

## 🔧 Управление

### Основные команды:
```bash
make help           # Показать все доступные команды
make start          # Запустить все сервисы
make stop           # Остановить все сервисы
make restart        # Перезапустить все сервисы
make status         # Показать статус контейнеров
make health         # Запустить проверку здоровья
make logs           # Показать логи всех сервисов
make clean          # Остановить и удалить ВСЕ данные (!)
```

### База данных:
```bash
make db-shell       # Подключиться к PostgreSQL
make db-backup      # Создать бэкап базы
make db-restore FILE=backup.sql  # Восстановить из бэкапа
```

### Redis:
```bash
make redis-shell    # Подключиться к Redis CLI
make redis-flush    # Очистить все данные Redis
```

### Быстрый доступ:
```bash
make grafana        # Открыть Grafana в браузере
make adminer        # Открыть Adminer в браузере
make redis-gui      # Открыть Redis Insight
make minio          # Открыть MinIO Console
```

## 🗄️ Структура базы данных

### Схемы:
- **agents** - агенты, их память и сессии
- **tasks** - задачи, зависимости, подзадачи
- **compliance** - стандарты и проверки соответствия
- **audit** - аудит всех событий системы
- **metrics** - метрики агентов, задач и системы

### Ключевые таблицы:
- `agents.agents` - информация об агентах
- `agents.memories` - память агентов (working, persistent, procedural)
- `tasks.tasks` - все задачи в системе
- `compliance.standards` - стандарты (ISO 27001, GDPR, NIST SSDF, CMMI)
- `compliance.checks` - результаты проверок соответствия
- `audit.events` - полный аудит действий

## 🔍 Мониторинг

### Grafana Dashboards:
После запуска доступны готовые дашборды для:
- Состояние инфраструктуры
- Метрики агентов  
- Производительность задач
- Compliance статус

### Prometheus Targets:
Автоматически собираются метрики с:
- PostgreSQL
- Redis  
- Docker containers
- Системные метрики
- Агенты (когда запущены)

## 📁 Структура проекта

```
galaxy-analytics-infrastructure/
├── docker-compose.yml          # Основная конфигурация Docker
├── .env                       # Переменные окружения
├── start.sh                   # Скрипт запуска
├── stop.sh                    # Скрипт остановки
├── health-check.sh            # Проверка состояния
├── Makefile                   # Удобные команды
├── init-scripts/
│   └── postgres/
│       └── 01-init-database.sql  # Инициализация БД
└── configs/
    ├── prometheus/
    ├── grafana/
    ├── loki/
    └── promtail/
```

## 🛡️ Безопасность

### Пароли по умолчанию:
⚠️ **ВАЖНО**: Измените все пароли в `.env` для production!

### Пользователи БД:
- `galaxy_admin` - администратор (полные права)
- `galaxy_agent_user` - для агентов (ограниченные права)  
- `galaxy_readonly_user` - только чтение

### Сети:
Все сервисы изолированы в Docker network `galaxy_network` (172.20.0.0/16).

## 🔧 Troubleshooting

### Проблемы с запуском:
```bash
# Проверить что Docker запущен
docker info

# Проверить свободное место (нужно >10GB)
df -h .

# Полная переустановка
make clean
make start
```

### Проблемы с подключением:
```bash
# Проверить статус всех сервисов
make health

# Посмотреть логи конкретного сервиса
make logs-postgres
make logs-redis
```

### Проблемы с производительностью:
```bash
# Посмотреть использование ресурсов
docker stats

# Перезапустить проблемные сервисы
docker-compose restart postgres
```

## 🚀 Следующие шаги

После успешного запуска инфраструктуры:

1. **Запустите агентов**: `npm run start:agents`
2. **Настройте Grafana**: импортируйте дашборды
3. **Создайте первую задачу**: через API или web интерфейс
4. **Настройте compliance правила**: добавьте свои стандарты

## 📞 Поддержка

### Полезные команды для диагностики:
```bash
make status         # Статус контейнеров
make health         # Полная проверка
make logs           # Все логи
docker system df    # Использование места
```

---

**🎉 Инфраструктура готова к разработке!**