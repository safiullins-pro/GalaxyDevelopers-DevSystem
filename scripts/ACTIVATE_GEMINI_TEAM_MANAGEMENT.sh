#!/bin/bash

# 🤖 Активация Gemini управления командой разработчиков
# Автоматический поиск и координация Frontend, Designer, DevOps

echo "🚀 Активация Gemini Command Center..."

# Путь к проекту
PROJECT_DIR="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
GEMINI_SCRIPTS="/Users/safiullins_pro/Scripts/gemini-triggers"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}📋 Инициализация проекта...${NC}"

# 1. Отправляем ТЗ в Gemini для анализа
echo -e "${BLUE}📤 Отправка технического задания в Gemini...${NC}"
$GEMINI_SCRIPTS/simple-gemini-process.sh "$PROJECT_DIR/TECHNICAL_SPECIFICATION.md" \
    "Создай детальный план поиска команды: Frontend Developer (React.js), UX/UI Designer (Dashboard), DevOps Engineer (Docker/nginx). Проанализируй требования и создай стратегию поиска кандидатов."

# 2. Анализ вакансий через Gemini
echo -e "${BLUE}🔍 Анализ job posts через Gemini...${NC}"
for job_file in "FRONTEND_JOB_POST.md" "DESIGNER_JOB_POST.md" "DEVOPS_JOB_POST.md"; do
    if [ -f "$PROJECT_DIR/$job_file" ]; then
        echo -e "  📄 Обрабатываю $job_file..."
        $GEMINI_SCRIPTS/simple-gemini-process.sh "$PROJECT_DIR/$job_file" \
            "Оптимизируй эту вакансию для максимальной привлекательности кандидатов. Добавь конкретные критерии отбора и процесс интервью."
    fi
done

# 3. Создание стратегии поиска
echo -e "${YELLOW}🎯 Gemini создает стратегию поиска команды...${NC}"
cat > "$PROJECT_DIR/GEMINI_SEARCH_STRATEGY.md" << 'EOF'
# 🤖 Gemini стратегия поиска команды

## Автоматизированный процесс

### 1. Поиск кандидатов
- **GitHub**: анализ репозиториев с React/Dashboard проектами
- **LinkedIn**: поиск по ключевым навыкам  
- **Dribbble/Behance**: дизайнеры с dashboard опытом
- **Stack Overflow**: активные разработчики

### 2. Автоматический скрининг
```bash
# Gemini оценивает кандидатов по критериям
gemini_score_candidate() {
    portfolio_quality * 0.4 +
    technology_match * 0.3 +  
    experience_relevance * 0.2 +
    communication_skills * 0.1
}
```

### 3. Интервью процесс
- **Техническое интервью**: автоматизированные вопросы
- **Практическое задание**: мини-проекты
- **Культурное соответствие**: работа в команде

### 4. Управление командой
- **Daily standups**: через Gemini координацию
- **Progress tracking**: автоматический мониторинг
- **Quality control**: code/design review

## Ожидаемые результаты
- **Timeline**: 15 дней до production ready UI
- **Quality**: Professional level dashboard
- **Budget**: $4,760-10,760 total
- **Team**: 3 профессионала (Frontend + Designer + DevOps)
EOF

# 4. Запуск мониторинга для команды
echo -e "${GREEN}📊 Активация системы мониторинга команды...${NC}"
if [ ! -f "$PROJECT_DIR/monitoring_server_fixed.py" ]; then
    echo -e "${RED}❌ Monitoring server не найден!${NC}"
    exit 1
fi

# Проверяем статус системы мониторинга
echo -e "${BLUE}🔍 Проверка статуса системы мониторинга...${NC}"
if [ -f "$PROJECT_DIR/monitoring_status.sh" ]; then
    bash "$PROJECT_DIR/monitoring_status.sh"
else
    echo -e "${YELLOW}⚠️ Система мониторинга требует запуска${NC}"
fi

# 5. Создание команд для Gemini
echo -e "${YELLOW}🤖 Создание Gemini команд управления...${NC}"
cat > "$PROJECT_DIR/GEMINI_COMMANDS.txt" << 'EOF'
# Команды для Gemini управления командой

## Поиск команды
GEMINI_SEARCH_FRONTEND: "Найди React.js разработчика с опытом WebSocket и dashboard"
GEMINI_SEARCH_DESIGNER: "Найди UX/UI дизайнера для технических dashboard интерфейсов"
GEMINI_SEARCH_DEVOPS: "Найди DevOps с опытом Python/FastAPI production deployments"

## Управление проектом
GEMINI_DAILY_STANDUP: "Проведи ежедневный стендап команды"
GEMINI_PROGRESS_CHECK: "Проверь прогресс по всем задачам"
GEMINI_QUALITY_REVIEW: "Проведи review кода и дизайна"

## Координация
GEMINI_SCHEDULE_MEETING: "Запланируй встречу команды"
GEMINI_RESOLVE_BLOCKER: "Помоги решить техническую проблему"
GEMINI_UPDATE_TIMELINE: "Обнови timeline проекта"
EOF

# 6. Финальная активация
echo -e "${GREEN}✅ Gemini Command Center активирован!${NC}"
echo ""
echo -e "${BLUE}🎯 Следующие шаги:${NC}"
echo -e "  1. Gemini анализирует ТЗ и создает план поиска"
echo -e "  2. Автоматический поиск кандидатов по всем каналам"
echo -e "  3. Скрининг и интервью через Gemini"
echo -e "  4. Координация работы команды"
echo -e "  5. Контроль качества и timeline"
echo ""
echo -e "${YELLOW}📊 Monitoring dashboard: http://localhost:8000${NC}"
echo -e "${YELLOW}📝 Project status: $PROJECT_DIR/GEMINI_SEARCH_STRATEGY.md${NC}"
echo ""
echo -e "${GREEN}🚀 Gemini готов командовать поиском и управлением команды!${NC}"