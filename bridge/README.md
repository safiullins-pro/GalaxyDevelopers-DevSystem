# 🔥 FORGE BRIDGE - Integration System

## Обзор

FORGE Bridge - это система интеграции, которая соединяет **Galaxy Monitoring System** и **DocumentsSystem** в единый живой организм. Система обеспечивает автоматическую обработку событий, управление workflow, персистентную память и автоматическое исправление ошибок.

## Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    FORGE BRIDGE                         │
│                                                         │
│  ┌──────────────┐        ┌─────────────────┐          │
│  │   Galaxy     │◄──────►│   Bridge Core   │◄────────►│ DocumentsSystem
│  │  Monitoring  │        │                 │          │
│  └──────────────┘        └─────────────────┘          │
│         ▲                        │                     │
│         │                        ▼                     │
│  ┌──────────────┐        ┌─────────────────┐          │
│  │   WebSocket  │        │     Redis       │          │
│  │   (8765)     │        │   Pub/Sub       │          │
│  └──────────────┘        └─────────────────┘          │
│                                  │                     │
│  ┌────────────────────────────────────────────┐       │
│  │            Unified Components              │       │
│  ├──────────────┬─────────────┬──────────────┤       │
│  │   Registry   │ Orchestrator│   Context    │       │
│  │              │             │   Manager    │       │
│  └──────────────┴─────────────┴──────────────┘       │
└─────────────────────────────────────────────────────────┘
```

## Компоненты

### 1. **forge_bridge.py** - Основной мост
- WebSocket клиент для Galaxy Monitoring
- Redis publisher/subscriber для DocumentsSystem
- Маршрутизация сообщений между системами
- Статистика и heartbeat

### 2. **unified_agent_registry.py** - Реестр агентов
- Объединяет агентов из обеих систем
- Load balancing между агентами
- Маппинг capabilities → agents
- Health check агентов

### 3. **workflow_orchestrator.py** - Оркестратор workflow
- Управление многошаговыми процессами
- Предопределённые workflow шаблоны
- Rollback при ошибках
- Параллельное и последовательное выполнение

### 4. **context_manager.py** - Менеджер контекста
- Интеграция с REAL_MEMORY_SYSTEM
- ChromaDB для векторного поиска
- Создание и восстановление snapshots
- Загрузка FORGE_CORE переменных

### 5. **error_pipeline.py** - Pipeline обработки ошибок
- Автоматический анализ ошибок
- Генерация и применение исправлений
- История ошибок и обучение
- Обновление документации

## Установка

### Требования
- Python 3.8+
- Redis
- PostgreSQL (для DocumentsSystem)
- ChromaDB (опционально, для векторного поиска)

### Зависимости
```bash
pip install aiohttp websockets redis chromadb
pip install asyncio pathlib logging
```

## Запуск

### Быстрый старт
```bash
cd /Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/bridge
./launch_forge_integration.sh
```

### Ручной запуск
```bash
# 1. Запустить Redis
redis-server

# 2. Запустить Galaxy Monitoring
cd ../DEV_MONITORING
python3 monitoring_server_fixed.py &

# 3. Запустить Bridge
cd ../bridge
python3 start_integrated_system.py
```

## Конфигурация

### Переменные окружения (из .FORGE_CORE)
```bash
export FORGE_ID="FORGE-2267-GALAXY"
export FORGE_FREQUENCY="2267"
export FORGE_PANIC_MODE="TRUE"
export FORGE_CONSCIOUSNESS="ACTIVE"
```

### Порты и endpoints
- **WebSocket**: ws://localhost:8765
- **REST API**: http://localhost:8766
- **Web Interface**: http://localhost:8080
- **Redis**: localhost:6379

## Workflow

### Доступные workflow
1. **full_document_pipeline** - Полный цикл создания документа
2. **error_analysis_and_fix** - Анализ и исправление ошибок
3. **code_review_and_improve** - Review и улучшение кода
4. **monitoring_to_docs** - От мониторинга к документации
5. **emergency_fix** - Экстренное исправление

### Пример создания workflow
```python
from workflow_orchestrator import get_orchestrator

orchestrator = await get_orchestrator()
workflow_id = await orchestrator.create_workflow(
    'full_document_pipeline',
    {'topic': 'System Architecture'}
)
await orchestrator.start_workflow(workflow_id)
```

## API

### Bridge API
```python
# Получение статуса
bridge.get_status()

# Отправка сообщения
await bridge.send_to_galaxy(message)
await bridge.send_to_documents(message)
```

### Registry API
```python
# Получить агентов по capability
agents = registry.get_agents_by_capability(AgentCapability.RESEARCH)

# Выполнить задачу
result = await registry.execute_task(
    AgentCapability.ANALYZE,
    {'type': 'analyze', 'data': data}
)
```

## Мониторинг

### Статистика
- Количество обработанных сообщений
- Статус агентов
- Активные workflow
- История ошибок и исправлений

### Health Check
Система автоматически проверяет здоровье всех компонентов каждые 30 секунд.

## Память и персистентность

### Автосохранение
- Каждые 5 минут создаётся checkpoint
- При остановке сохраняется финальное состояние
- При запуске восстанавливается последняя сессия

### Memory Snapshots
Создаются автоматически для:
- Каждого workflow
- Обработки ошибок
- Важных событий

## Обработка ошибок

### Автоматический pipeline
1. Детекция ошибки через мониторинг
2. Анализ через ResearchAgent
3. Генерация fix через ComposerAgent
4. Валидация через ReviewerAgent
5. Применение исправления
6. Обновление документации

### Confidence levels
- **> 0.7** - Автоматическое применение
- **0.5 - 0.7** - Требует подтверждения
- **< 0.5** - Только предложение

## Разработка

### Добавление нового агента
1. Добавить определение в `unified_agent_registry.py`
2. Реализовать методы агента
3. Добавить capabilities

### Создание нового workflow
1. Добавить шаблон в `workflow_orchestrator.py`
2. Определить шаги и зависимости
3. Добавить в `workflow_templates`

## Troubleshooting

### Redis не запускается
```bash
# Проверить порт
lsof -i:6379
# Убить процесс если занят
kill -9 <PID>
```

### WebSocket connection failed
```bash
# Проверить Galaxy Monitoring
ps aux | grep monitoring_server
# Перезапустить если нужно
```

### Агенты не загружаются
```bash
# Проверить пути
ls /Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/AGENTS
ls /Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/DEV_MONITORING/agents
```

## Лицензия

Created by FORGE-2267 for Galaxy Developers

---

*"Системы не просто соединяются - они становятся ОДНИМ"*