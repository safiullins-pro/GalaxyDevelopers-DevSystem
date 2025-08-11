# GalaxyDevelopers DevSystem - Project Context

## 🚨 КРИТИЧЕСКОЕ ПРАВИЛО
**НИКОГДА НЕ СОЗДАВАТЬ НОВЫЕ ФАЙЛЫ И ПАПКИ БЕЗ ЯВНОГО РАЗРЕШЕНИЯ!**
Это правило должно ВСЕГДА быть первым в любом ответе при работе с этим проектом.

## Автоматический контекст проекта
При работе с этим проектом ВСЕГДА:
1. Проверяй текущую структуру папок перед любыми изменениями
2. Используй только существующие директории
3. Спрашивай разрешение перед созданием новых файлов/папок
4. После успешных тестов - коммить и пуш на GitHub

## Структура проекта
```
/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/
├── server/           # Серверная часть
│   ├── GalaxyDevelopersAI-backend.js    # Express сервер, порт 37777
│   └── GalaxyDevelopersAI-key-rotator.js # Ротация API ключей
├── interface/        # Веб интерфейс
│   └── GalaxyDevelopersAI-web.html      # Доступ: http://127.0.0.1:37777
├── connectors/       # Интеграции
│   ├── iterm2-integration.py            # iTerm2 Python API
│   └── ScreenShots/                     # Хранилище скриншотов
├── resources/        # Ресурсы
│   ├── available-models.json            # Список моделей Gemini
│   └── node_modules/                    # NPM зависимости
├── scripts/          # Утилиты
│   ├── send-to-claude.sh               # Отправка скриншотов в Claude
│   └── setup-iterm2.sh                 # Настройка iTerm2
├── validators/       # Тестирование
│   └── test-models.js                  # Валидатор моделей
└── docs/            # Документация
    └── CLAUDE.md                        # Полная документация (импорт)
```

## Критические файлы и пути
- **Backend**: `/server/GalaxyDevelopersAI-backend.js` - НЕ ломать пути!
- **Web UI**: `/interface/GalaxyDevelopersAI-web.html`
- **Screenshots**: `/connectors/ScreenShots/`
- **LaunchAgent**: `~/Library/LaunchAgents/com.galaxydevelopers.ai.backend.plist`
- **Port**: 37777 (ВСЕГДА)
- **GitHub**: https://github.com/safiullins-pro/GalaxyDevelopers-DevSystem

## API Endpoints
- `POST /chat` - основной чат (prompt, instruction, context, model)
- `GET /models` - список моделей
- `POST /screenshot` - создание скриншота
- `GET /mcp/screenshot` - MCP endpoint для AI агентов
- `GET /webhook/status` - статус для iTerm2

## Команды управления сервисом
```bash
# Перезапуск
launchctl kickstart -k gui/$(id -u)/com.galaxydevelopers.ai.backend

# Логи
tail -f /tmp/galaxydevelopers-ai-backend.error.log

# Проверка статуса
curl http://127.0.0.1:37777
```

## Рабочий процесс
1. ВСЕГДА начинай с проверки структуры: `ls -la`
2. НЕ создавай файлы без разрешения
3. Используй TodoWrite для планирования задач
4. После изменений тестируй работоспособность
5. Коммить и пуш после успешных тестов

## Импорт полной документации
@/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/docs/CLAUDE.md

## Git правила
- Коммить после каждого успешного функционала
- Всегда пушить на GitHub
- Commit message должен быть информативным
- НЕ коммитить API ключи и секреты

## Технологический стек
- Node.js + Express
- Google Gemini API (@google/genai)
- macOS launchd services  
- iTerm2 Python API
- Stateless architecture (без сессий)

## Особенности реализации
- 14 API ключей с автоматической ротацией
- Каждый запрос = новый экземпляр GoogleGenAI
- Нет хранения истории диалогов
- Screenshots сохраняются с timestamp
- Webhook интеграция для iTerm2

## iTerm2 Интеграция
**Настройки iTerm2 (Preferences → General → Magic):**
- ✅ Enable Python API - ВКЛЮЧЕНО
- ✅ Allow all apps to connect - ВКЛЮЧЕНО  
- ✅ Custom Python API Scripts Folder → `/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/connectors/`

После настройки перезапустить iTerm2 и запустить:
```bash
python3 /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/connectors/iterm2-integration.py
```

## Текущий статус проекта (11.08.2025)
- ✅ Проект полностью реструктурирован по папкам
- ✅ Git репозиторий создан: https://github.com/safiullins-pro/GalaxyDevelopers-DevSystem
- ✅ Сервис работает на порту 37777
- ✅ Веб-интерфейс доступен: http://127.0.0.1:37777
- ✅ Python модуль iterm2 установлен: `pip3 install iterm2`
- ⏳ iTerm2 настройки: включить Custom Python API Scripts Folder
- ⏳ Запустить iterm2-integration.py после перезапуска iTerm2

## Отладка
При ошибках проверять:
1. Работает ли сервис: `launchctl list | grep galaxydevelopers`
2. Логи: `/tmp/galaxydevelopers-ai-backend.error.log`
3. Доступность порта: `lsof -i :37777`
4. Пути к файлам после реструктуризации
5. Состояние ключей: `.galaxydevelopers-ai-key-state.json`