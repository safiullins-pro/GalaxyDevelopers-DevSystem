# MASTER PLAN: Централизованная система управления сервисами

## EXECUTIVE SUMMARY
Основываясь на анализе этапа 1, создаём unified orchestration solution для управления **13 сервисами** системы GalaxyDevelopers AI на **8 портах** с решением критических проблем и созданием **single-command startup**.

## ВЫБРАННАЯ АРХИТЕКТУРА: **Enhanced Shell Script Orchestration + Service Registry**

### Обоснование выбора:
- **Простота управления**: Использует существующие 40+ shell scripts как foundation
- **Минимальные изменения**: Работает с текущей инфраструктурой без major refactoring
- **Масштабируемость**: Легко добавлять новые сервисы через registry pattern
- **Мониторинг**: Интеграция с существующей DEV_MONITORING системой
- **Отказоустойчивость**: Health checks и automatic restart capability

## АРХИТЕКТУРНОЕ РЕШЕНИЕ:

### Core Components:
```
GALAXY_ORCHESTRATOR/
├── galaxy-master.sh              # 🎯 ГЛАВНЫЙ КОНТРОЛЛЕР
├── config/
│   ├── services.yaml             # Реестр всех сервисов
│   ├── ports.yaml                # Управление портами
│   └── dependencies.yaml         # Граф зависимостей
├── modules/
│   ├── service-manager.sh        # Управление сервисами
│   ├── health-monitor.sh         # Health check система
│   ├── dependency-resolver.sh    # Разрешение зависимостей
│   └── port-manager.sh           # Управление портами
├── services/
│   ├── backend/                  # Service wrappers
│   ├── memory-api/
│   ├── experience-api/
│   ├── monitoring/
│   └── [other services]/
└── logs/                         # Централизованные логи
```

## ПЛАН РЕАЛИЗАЦИИ:

### Phase 1: Foundation Setup (Day 1) ⚡
#### Morning (4 hours):
- [ ] **09:00-11:00: Service Registry Creation**
  - Создать `config/services.yaml` с полным описанием всех 13 сервисов
  - Решить конфликт портов (Experience API: 5555 → 5556)
  - Определить startup order и dependencies

- [ ] **11:00-13:00: Core Orchestration Engine**
  - Создать `galaxy-master.sh` - главный контроллер
  - Реализовать `modules/service-manager.sh` для управления сервисами
  - Интеграция с existing scripts в `/SCRIPTS/`

#### Afternoon (4 hours):
- [ ] **14:00-16:00: Health Check System**
  - Создать `modules/health-monitor.sh`
  - Интеграция с существующими `/health` endpoints
  - Real-time status dashboard через DEV_MONITORING

- [ ] **16:00-18:00: Dependency Resolution**
  - Создать `modules/dependency-resolver.sh`
  - Автоматический startup order: Database → Redis → Memory API → Backend → Frontend
  - Graceful shutdown в обратном порядке

### Phase 2: Service Integration (Day 2) ⚡
#### Full Day (8 hours):
- [ ] **09:00-11:00: Backend Services Integration**
  - Wrapper для `SERVER/GalaxyDevelopersAI-backend.js`
  - Автозапуск Memory API integration
  - Environment standardization

- [ ] **11:00-13:00: Python Services Integration**
  - Memory API (37778): health check + auto-restart
  - Experience API (5556): port conflict resolution
  - Voice Storage (5557): новый порт
  - DEV_MONITORING integration

- [ ] **14:00-16:00: AI Document Services**
  - DOC_SYSTEM services wrapper
  - STANDARTS_AI_DOCUMENT_SYSTEM integration
  - Port standardization for all AI services

- [ ] **16:00-18:00: Testing & Validation**
  - End-to-end system startup test
  - Graceful shutdown test
  - Failure recovery test
  - Performance validation

### Phase 3: Advanced Features (Day 3) ⚡
- [ ] **Auto-scaling policies** для сервисов под нагрузкой
- [ ] **Backup automation** для критических данных
- [ ] **Security hardening** integration с Lazarus audit
- [ ] **Performance optimization** и resource limits
- [ ] **Documentation finalization** и runbooks

## DETAILED IMPLEMENTATION:

### 1. Service Registry Format (`config/services.yaml`):
```yaml
services:
  backend:
    name: "Galaxy Backend API"
    type: "nodejs"
    file: "SERVER/GalaxyDevelopersAI-backend.js"
    port: 3000
    health_endpoint: "/health"
    dependencies: ["memory-api", "postgres", "redis"]
    auto_restart: true
    critical: true
    
  memory-api:
    name: "Memory API"
    type: "python"
    file: "MEMORY/memory_api.py"
    port: 37778
    health_endpoint: "/health"
    dependencies: ["postgres"]
    auto_restart: true
    critical: true
    
  experience-api:
    name: "Experience API"
    type: "python"
    file: "src/experience_api.py"
    port: 5556  # CHANGED from 5555 to resolve conflict
    health_endpoint: "/api/health"
    dependencies: []
    auto_restart: true
    critical: false
```

### 2. Main Orchestrator (`galaxy-master.sh`):
```bash
#!/bin/bash
# 🎯 GALAXY ORCHESTRATOR - Single Command System Control

GALAXY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$GALAXY_ROOT/modules/service-manager.sh"
source "$GALAXY_ROOT/modules/health-monitor.sh"
source "$GALAXY_ROOT/modules/dependency-resolver.sh"

case "$1" in
    start)
        echo "🚀 Starting Galaxy Developer System..."
        start_all_services
        ;;
    stop)
        echo "🛑 Stopping Galaxy Developer System..."
        stop_all_services
        ;;
    restart)
        echo "🔄 Restarting Galaxy Developer System..."
        stop_all_services
        start_all_services
        ;;
    status)
        echo "📊 Galaxy System Status:"
        show_system_status
        ;;
    health)
        echo "💓 System Health Check:"
        run_health_checks
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|health}"
        exit 1
        ;;
esac
```

### 3. Port Conflict Resolution:
```yaml
port_assignments:
  3000: "backend-api"           # Main backend
  5432: "postgresql"            # Database
  6379: "redis"                 # Cache
  5555: "voice-storage"         # Voice (original)
  5556: "experience-api"        # Experience (moved)
  8765: "monitoring-ws"         # Monitoring WebSocket
  8766: "monitoring-http"       # Monitoring HTTP
  37778: "memory-api"           # Memory API
```

## EXPECTED DELIVERABLES:

### После реализации получим:
✅ **Unified Control Interface:**
```bash
# Одна команда запускает всю систему
./galaxy-master.sh start

# Проверка статуса всех сервисов
./galaxy-master.sh status

# Health check всей системы
./galaxy-master.sh health

# Graceful shutdown
./galaxy-master.sh stop
```

✅ **Operational Excellence:**
- **Zero-downtime deployments** через rolling restart
- **Automatic health checks** каждые 30 секунд
- **Resource monitoring** через DEV_MONITORING integration
- **Backup procedures** для критических данных

✅ **Developer Experience:**
- **Simple development setup**: один скрипт для старта
- **Consistent environments** через standardized configuration
- **Easy debugging** через централизованные логи
- **Fast iteration cycles** через automatic restart

✅ **System Reliability:**
- **Dependency-aware startup** - правильный порядок запуска
- **Automatic failure recovery** - перезапуск упавших сервисов
- **Port conflict resolution** - автоматическое управление портами
- **Resource isolation** - каждый сервис в своем контексте

## RISK MITIGATION:
- [🔴] **Риск**: Existing scripts compatibility
  - **План митигации**: Использовать existing scripts как base, минимальные изменения
- [🔴] **Риск**: Service startup failures
  - **План митигации**: Health checks + retry logic + fallback procedures
- [🟡] **Риск**: Performance overhead
  - **План митигации**: Lightweight shell-based solution, minimal resource usage

## SUCCESS METRICS:
- **Время запуска системы**: < 60 секунд (all 13 services)
- **Availability**: > 99.9% (через auto-restart)
- **Recovery time**: < 30 секунд (automatic failure detection)
- **Developer startup time**: < 5 минут (from zero to running system)

## INTEGRATION WITH EXISTING SYSTEMS:

### Leverage Existing Assets:
✅ **AUTOSTART_ALL_SERVICES.sh** → Foundation для galaxy-master.sh
✅ **DEV_MONITORING system** → Health check и monitoring integration
✅ **Memory API автозапуск** → Pattern для dependency management
✅ **Existing health endpoints** → Health check system base

### Minimal Impact Changes:
- Experience API: только изменение порта 5555 → 5556
- Voice Storage: остается на 5555 (был первым)
- Все остальные сервисы: БЕЗ ИЗМЕНЕНИЙ, только orchestration wrapper

## TIMELINE SUMMARY:
- **Day 1**: Foundation + Registry + Health Checks ✅
- **Day 2**: Service Integration + Testing ✅  
- **Day 3**: Advanced Features + Documentation ✅

**РЕЗУЛЬТАТ**: Полностью работающая централизованная система управления всеми 13 сервисами Galaxy AI System с **single-command control** и **automatic reliability**.

**ГОТОВНОСТЬ К РЕАЛИЗАЦИИ**: ✅ **ПЛАН УТВЕРЖДЕН** - переходим к implementation!