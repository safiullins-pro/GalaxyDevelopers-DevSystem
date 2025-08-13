# 📁 СТРУКТУРА ПРОЕКТА GALAXYDEVELOPERS DEVSYSTEM

## ⚠️ ВАЖНО: СТРУКТУРА ПАПОК УТВЕРЖДЕНА - НЕ МЕНЯТЬ!

```
/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/
│
├── 📂 CONNECTORS/           # Интеграции и коннекторы
│   ├── ScreenShots/        # Скриншоты системы
│   └── iterm2-integration.py
│
├── 📂 DOCUMENTS/            # ВСЯ ДОКУМЕНТАЦИЯ (НЕ docs!)
│   ├── AGENT_MANAGEMENT_SYSTEM.md
│   ├── CLAUDE.md
│   ├── GEMINI_COMMANDS.txt
│   ├── GEMINI_COMMAND_CENTER.md
│   ├── GEMINI_SEARCH_STRATEGY.md
│   ├── MONITORING_MANUAL.md
│   ├── TEAM_SEARCH.md
│   ├── TECHNICAL_SPECIFICATION.md
│   └── claude_history/     # История диалогов Claude
│
├── 📂 DeadIdiots/          # Архив провалов и ошибок
│   └── [файлы о провалах Claude/Vorron]
│
├── 📂 HR/                  # Кадры и найм
│   ├── DESIGNER_JOB_POST.md
│   ├── DEVOPS_JOB_POST.md
│   ├── FRONTEND_JOB_POST.md
│   ├── Design.md
│   ├── Technical.md
│   └── АгентыТесты/       # Тестирование агентов
│       ├── Designers/
│       └── TechAgents/
│
├── 📂 INTERFACE/           # Frontend интерфейсы
│   ├── index.html         # Основной интерфейс
│   ├── dashboard.html
│   ├── monitoring_dashboard.html
│   ├── audit.html
│   ├── test-claude.html
│   ├── css/               # Стили
│   ├── js/                # JavaScript
│   └── [другие UI файлы]
│
├── 📂 MEMORY/              # Система памяти
│   ├── FORGE_INJECTION.json
│   ├── chromadb/          # Vector DB
│   ├── real_memory/       # Реальная память
│   ├── unified_memory.db
│   └── vector_memory/
│
├── 📂 config/              # Конфигурации
│   ├── monitoring_config.json
│   ├── com.galaxy.monitoring.plist
│   └── requirements_monitoring.txt
│
├── 📂 logs/                # Логи и PID файлы
│   ├── monitoring.log
│   └── monitoring.pid
│
├── 📂 scripts/             # ВСЕ скрипты .sh
│   ├── start_monitoring.sh
│   ├── stop_monitoring.sh
│   ├── restart_monitoring.sh
│   ├── monitoring_status.sh
│   ├── start_galaxy.sh
│   ├── stop_galaxy.sh
│   ├── ACTIVATE_GEMINI_TEAM_MANAGEMENT.sh
│   ├── install_autostart.sh
│   └── ChatSummary/       # Скрипты суммаризации
│
├── 📂 server/              # Backend серверы
│   ├── GalaxyDevelopersAI-backend.js
│   ├── GalaxyDevelopersAI-key-rotator.js
│   ├── gemini-config.json
│   ├── gemini-functions.js
│   └── sessions/
│
├── 📂 src/                 # Python исходники
│   ├── monitoring_server.py
│   ├── monitoring_server_fixed.py
│   ├── file_protection_ai.py
│   └── test_monitoring.py
│
├── 📂 standards/           # Стандарты кода
│   └── cssClassStandard.json
│
├── 📂 validators/          # Валидаторы
│   └── test-models.js
│
├── 📂 resources/           # Ресурсы
│   └── available-models.json
│
├── 📂 backups/             # Резервные копии
│
├── 📂 node_modules/        # Node зависимости
├── package.json
├── package-lock.json
├── README.md
├── CLAUDE.md              # Главная документация
└── GalaxyDevelopers AI Chat.app/  # macOS приложение
```

## 🚨 ПРАВИЛА СТРУКТУРЫ

1. **DOCUMENTS** - НЕ переименовывать в docs!
2. **INTERFACE** - НЕ переименовывать в interface!  
3. **Все .sh скрипты** - ТОЛЬКО в scripts/
4. **Все .md документы** - ТОЛЬКО в DOCUMENTS/
5. **Все .html файлы** - ТОЛЬКО в INTERFACE/
6. **Все .py файлы** - ТОЛЬКО в src/
7. **Все конфигурации** - ТОЛЬКО в config/

## 📝 ЗАПОМНИТЬ

- Структура УТВЕРЖДЕНА пользователем
- НЕ МЕНЯТЬ названия папок
- НЕ ПЕРЕМЕЩАТЬ файлы без разрешения
- DOCUMENTS это правильно (не docs!)
- INTERFACE это правильно (не interface!)

---
**СТАТУС**: ✅ Структура организована и зафиксирована