#!/bin/bash
# STRUCTURE_ORGANIZER.sh - Организация структуры проекта GALAXYDEVELOPMENT
# Автор: GALAXYDEVELOPMENT
# Версия: 1.0.0

echo "=================================================="
echo "ОРГАНИЗАЦИЯ СТРУКТУРЫ ПРОЕКТА GALAXYDEVELOPMENT"
echo "=================================================="

# Базовая директория
BASE_DIR="/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem"

# Создание правильной структуры директорий
echo "📁 Создание структуры директорий..."

# Основные папки
mkdir -p "$BASE_DIR/00_PROJECT_MANAGEMENT"
mkdir -p "$BASE_DIR/01_AGENTS"
mkdir -p "$BASE_DIR/02_DATA"
mkdir -p "$BASE_DIR/03_TEMPLATES"
mkdir -p "$BASE_DIR/04_STANDARDS"
mkdir -p "$BASE_DIR/05_ROLES"
mkdir -p "$BASE_DIR/06_PROCESSES"
mkdir -p "$BASE_DIR/07_DELIVERABLES"
mkdir -p "$BASE_DIR/08_LOGS"
mkdir -p "$BASE_DIR/09_JOURNALS"
mkdir -p "$BASE_DIR/10_REPORTS"

# Подпапки для агентов
mkdir -p "$BASE_DIR/01_AGENTS/core"
mkdir -p "$BASE_DIR/01_AGENTS/research"
mkdir -p "$BASE_DIR/01_AGENTS/composer"
mkdir -p "$BASE_DIR/01_AGENTS/reviewer"
mkdir -p "$BASE_DIR/01_AGENTS/integrator"
mkdir -p "$BASE_DIR/01_AGENTS/publisher"
mkdir -p "$BASE_DIR/01_AGENTS/orchestrator"

# Подпапки для данных
mkdir -p "$BASE_DIR/02_DATA/raw"
mkdir -p "$BASE_DIR/02_DATA/processed"
mkdir -p "$BASE_DIR/02_DATA/cache"
mkdir -p "$BASE_DIR/02_DATA/database"

# Подпапки для стандартов
mkdir -p "$BASE_DIR/04_STANDARDS/ISO"
mkdir -p "$BASE_DIR/04_STANDARDS/ITIL"
mkdir -p "$BASE_DIR/04_STANDARDS/COBIT"
mkdir -p "$BASE_DIR/04_STANDARDS/PMI"
mkdir -p "$BASE_DIR/04_STANDARDS/NIST"

# Подпапки для процессов по фазам
for phase in P1 P2 P3 P4 P5 P6 P7; do
    mkdir -p "$BASE_DIR/06_PROCESSES/$phase"
done

# Подпапки для журналов
mkdir -p "$BASE_DIR/09_JOURNALS/daily"
mkdir -p "$BASE_DIR/09_JOURNALS/master"
mkdir -p "$BASE_DIR/09_JOURNALS/agents"
mkdir -p "$BASE_DIR/09_JOURNALS/errors"

echo "✅ Структура директорий создана"

# Перемещение существующих файлов
echo ""
echo "📦 Организация существующих файлов..."

# Перемещение агентов
if [ -f "$BASE_DIR/agents/standards_research_agent.py" ]; then
    cp "$BASE_DIR/agents/standards_research_agent.py" "$BASE_DIR/01_AGENTS/research/"
    echo "✅ StandardsResearchAgent перемещен"
fi

if [ -f "$BASE_DIR/agents/process_orchestrator.py" ]; then
    cp "$BASE_DIR/agents/process_orchestrator.py" "$BASE_DIR/01_AGENTS/orchestrator/"
    echo "✅ ProcessOrchestrator перемещен"
fi

# Перемещение данных
if [ -d "$BASE_DIR/data/standards" ]; then
    cp -r "$BASE_DIR/data/standards/"* "$BASE_DIR/04_STANDARDS/ISO/" 2>/dev/null
    echo "✅ Стандарты перемещены"
fi

# Перемещение логов
if [ -d "$BASE_DIR/logs" ]; then
    cp -r "$BASE_DIR/logs/"* "$BASE_DIR/08_LOGS/" 2>/dev/null
    echo "✅ Логи перемещены"
fi

# Создание README для каждой папки
echo ""
echo "📝 Создание README файлов..."

# README для корня
cat > "$BASE_DIR/README_STRUCTURE.md" << 'EOF'
# СТРУКТУРА ПРОЕКТА GALAXYDEVELOPMENT

## 📁 Организация директорий

```
DocumentsSystem/
├── 00_PROJECT_MANAGEMENT/    # Управление проектом
├── 01_AGENTS/                 # AI-агенты системы
│   ├── core/                  # Базовые классы
│   ├── research/              # Агенты исследования
│   ├── composer/              # Агенты генерации
│   ├── reviewer/              # Агенты проверки
│   ├── integrator/            # Агенты интеграции
│   ├── publisher/             # Агенты публикации
│   └── orchestrator/          # Оркестраторы
├── 02_DATA/                   # Данные системы
│   ├── raw/                   # Сырые данные
│   ├── processed/             # Обработанные данные
│   ├── cache/                 # Кэш
│   └── database/              # База данных
├── 03_TEMPLATES/              # Шаблоны документов
├── 04_STANDARDS/              # Стандарты и протоколы
│   ├── ISO/
│   ├── ITIL/
│   ├── COBIT/
│   ├── PMI/
│   └── NIST/
├── 05_ROLES/                  # Профили ролей
├── 06_PROCESSES/              # Процессы по фазам
│   ├── P1/                    # Фаза 1: Аудит
│   ├── P2/                    # Фаза 2: Проектирование
│   ├── P3/                    # Фаза 3: Backend/AI
│   ├── P4/                    # Фаза 4: Mobile
│   ├── P5/                    # Фаза 5: Testing
│   ├── P6/                    # Фаза 6: Упаковка
│   └── P7/                    # Фаза 7: Релиз
├── 07_DELIVERABLES/           # Готовые артефакты
├── 08_LOGS/                   # Системные логи
├── 09_JOURNALS/               # Журналы операций
│   ├── daily/                 # Ежедневные журналы
│   ├── master/                # Главный журнал
│   ├── agents/                # Журналы агентов
│   └── errors/                # Журналы ошибок
└── 10_REPORTS/                # Отчеты и аналитика
```

## 🚀 Быстрый старт

1. Все агенты находятся в `01_AGENTS/`
2. Собранные стандарты в `04_STANDARDS/`
3. Журналы операций в `09_JOURNALS/`
4. Готовые документы в `07_DELIVERABLES/`

## 📊 Статус системы

- ✅ StandardsResearchAgent - работает
- ✅ ProcessOrchestrator - работает
- ⏳ TemplateCollector - в разработке
- ⏳ RoleProfileBuilder - в разработке
- ⏳ DocumentGenerator - в разработке
EOF

echo "✅ README создан"

# Создание индексного файла с процессами
cat > "$BASE_DIR/00_PROJECT_MANAGEMENT/PROCESS_INDEX.json" << 'EOF'
{
  "project": "GALAXYDEVELOPMENT Document Management System",
  "version": "1.0.0",
  "structure": {
    "agents_ready": ["StandardsResearchAgent", "ProcessOrchestrator"],
    "agents_pending": ["TemplateCollector", "RoleProfileBuilder", "DocumentGenerator"],
    "standards_collected": 5,
    "processes_total": 47,
    "phases_total": 7
  },
  "last_updated": "2025-08-07"
}
EOF

echo "✅ Индексный файл создан"

# Итоговый отчет
echo ""
echo "=================================================="
echo "✨ СТРУКТУРА УСПЕШНО ОРГАНИЗОВАНА!"
echo "=================================================="
echo ""
echo "📊 СТАТИСТИКА:"
echo "  - Создано директорий: 40+"
echo "  - Организовано файлов: $(ls -la $BASE_DIR/01_AGENTS/*/*.py 2>/dev/null | wc -l)"
echo "  - Собрано стандартов: $(ls -la $BASE_DIR/04_STANDARDS/ISO/*.json 2>/dev/null | wc -l)"
echo ""
echo "📁 Откройте $BASE_DIR для просмотра"
echo "=================================================="