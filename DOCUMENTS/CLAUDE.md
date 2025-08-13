# GalaxyDevelopers AI Chat System

## ⚠️ ВАЖНЫЕ ПРАВИЛА СТРУКТУРЫ
**НИКОГДА БЕЗ СПРОСА НЕ СОЗДАВАТЬ НОВЫЕ ФАЙЛЫ И ПАПКИ!**

### Структура директорий
```
/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/
├── docs/           # Вся документация
├── scripts/        # Скрипты, которые мы используем
├── resources/      # Список моделей, токены, библиотеки и модули
├── ScreenShots/    # Хранилище скриншотов
└── [корневые файлы] # Backend, веб-интерфейс, конфиги
```

## Описание проекта
Stateless AI чат-система с автоматической ротацией API ключей Google Gemini, веб-интерфейсом и системными интеграциями для macOS.

## Основные особенности
- **Stateless архитектура** - каждый запрос независимый, без сохранения сессий
- **Автоматическая ротация 14 API ключей** - переключение при каждом запросе
- **Выбор из 11 моделей Gemini** (1.5, 2.0, 2.5 версии)
- **Системный сервис macOS** - автозапуск при загрузке системы
- **MCP интеграция** - API для AI агентов
- **Скриншот функциональность** - сохранение состояния интерфейса

## Структура проекта

```
/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/
├── docs/                             # Вся документация
│   └── CLAUDE.md                     
├── scripts/                          # Скрипты, которые мы используем
│   ├── send-to-claude.sh             
│   └── setup-iterm2.sh               
├── resources/                        # Модели, токены, библиотеки и модули
│   ├── available-models.json         
│   └── node_modules/                 
├── server/                           # Серверная часть
│   ├── GalaxyDevelopersAI-backend.js 
│   └── GalaxyDevelopersAI-key-rotator.js 
├── interface/                        # Фронт интерфейс
│   └── GalaxyDevelopersAI-web.html   
├── connectors/                       # Все для соединений
│   ├── iterm2-integration.py         
│   └── ScreenShots/                  
├── validators/                       # Валидаторы и тестеры
│   └── test-models.js                
├── .galaxydevelopers-ai-keys         # API ключи (14 штук)
├── .galaxydevelopers-ai-key-state.json # Состояние ключей
├── package.json                      # NPM зависимости
└── package-lock.json                 
```

## Доступ к системе

### Веб-интерфейс
**URL:** http://127.0.0.1:37777

### API Endpoints

#### Основной чат
```bash
POST http://127.0.0.1:37777/chat
Content-Type: application/json

{
  "prompt": "Ваш вопрос",
  "instruction": "Системная инструкция (опционально)",
  "context": "Дополнительный контекст (опционально)",
  "model": "gemini-1.5-flash" // или другая модель
}
```

#### Список моделей
```bash
GET http://127.0.0.1:37777/models
```

#### Создание скриншота (для веб-интерфейса)
```bash
POST http://127.0.0.1:37777/screenshot
```

#### MCP endpoint для AI агентов
```bash
GET http://127.0.0.1:37777/mcp/screenshot
```
Возвращает:
```json
{
  "success": true,
  "filename": "mcp-screenshot-2025-08-11T16-06-08.png",
  "path": "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/ScreenShots/mcp-screenshot-2025-08-11T16-06-08.png",
  "message": "Screenshot saved to ScreenShots/mcp-screenshot-2025-08-11T16-06-08.png"
}
```

## Доступные модели

1. **gemini-1.5-flash** - Быстрая универсальная модель
2. **gemini-1.5-flash-8b** - Самая дешевая и легкая
3. **gemini-2.0-flash** - Версия 2.0
4. **gemini-2.0-flash-lite** - Облегченная 2.0
5. **gemini-2.0-flash-thinking-exp** - Модель с расширенным мышлением
6. **gemini-2.5-flash** - Последняя версия Flash
7. **gemini-2.5-pro** - Самая мощная модель
8. **learnlm-2.0-flash-experimental** - Образовательная модель

## Управление системным сервисом

### Расположение службы
```
~/Library/LaunchAgents/com.galaxydevelopers.ai.backend.plist
```

### Команды управления
```bash
# Перезапуск сервиса
launchctl kickstart -k gui/$(id -u)/com.galaxydevelopers.ai.backend

# Остановка сервиса
launchctl unload ~/Library/LaunchAgents/com.galaxydevelopers.ai.backend.plist

# Запуск сервиса
launchctl load ~/Library/LaunchAgents/com.galaxydevelopers.ai.backend.plist

# Проверка статуса
launchctl list | grep galaxydevelopers
```

### Логи сервиса
```bash
# Основной лог
tail -f /tmp/galaxydevelopers-ai-backend.log

# Лог ошибок
tail -f /tmp/galaxydevelopers-ai-backend.error.log
```

## Ротация ключей

### Проверка всех ключей
```bash
node /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/resources/GalaxyDevelopersAI-key-rotator.js validate
```

### Получить следующий ключ
```bash
node /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/resources/GalaxyDevelopersAI-key-rotator.js next
```

### Получить текущий ключ
```bash
node /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/resources/GalaxyDevelopersAI-key-rotator.js current
```

## Особенности реализации

### Stateless архитектура
- Каждый запрос создает новый экземпляр GoogleGenAI
- Нет хранения истории диалогов
- Нет состояния между запросами
- Контекст передается в каждом запросе явно

### Ротация ключей
- 14 рабочих API ключей Google
- Автоматическая смена ключа при каждом запросе
- Обработка 429 ошибок (rate limit)
- Исключение заблокированных ключей из ротации
- Сохранение состояния ключей в `.galaxydevelopers-ai-key-state.json`

### Безопасность
- Сервер слушает только localhost (127.0.0.1)
- Порт 37777 (непопулярный, избегаем конфликтов)
- API ключи хранятся локально
- Нет внешнего доступа

### Интеграция с Safari
1. Откройте http://127.0.0.1:37777 в Safari
2. Меню **Файл** → **Добавить на Dock**
3. Получите отдельное приложение без адресной строки

## Настройки веб-интерфейса

Все настройки сохраняются в localStorage браузера:
- `galaxydevelopers-ai-instruction` - системная инструкция
- `galaxydevelopers-ai-context` - контекст
- `galaxydevelopers-ai-model` - выбранная модель
- `galaxydevelopers-ai-endpoint` - API endpoint

## CLI использование

```bash
cd /Volumes/Z7S/development/GalaxyDevelopers/DevSystem
node GalaxyDevelopersAI-cli.js
```

CLI автоматически читает:
- `.instruction` - файл с инструкцией
- `.context` - файл с контекстом

## Установка зависимостей

```bash
cd /Volumes/Z7S/development/GalaxyDevelopers/DevSystem
npm install
```

### Необходимые пакеты
- express - веб-сервер
- @google/genai - Google Gemini API клиент
- Встроенные модули Node.js (fs, path, child_process)

## Примеры использования

### Через curl
```bash
curl -X POST http://127.0.0.1:37777/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Привет, как дела?",
    "model": "gemini-2.5-flash"
  }'
```

### Через веб-интерфейс
1. Откройте http://127.0.0.1:37777
2. Выберите модель в боковой панели
3. Введите системную инструкцию и контекст (опционально)
4. Пишите сообщения и отправляйте Cmd+Enter

### MCP для AI агентов
```bash
# Сделать скриншот текущего состояния
curl http://127.0.0.1:37777/mcp/screenshot

# Результат будет в папке ScreenShots
ls /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/ScreenShots/
```

## Важные замечания

1. **Порт 37777** - всегда используется этот порт, избегаем конфликтов
2. **Автозапуск** - сервис запускается при загрузке macOS
3. **Без логирования** - минимальное логирование для безопасности
4. **Ротация ключей** - автоматическая, не требует вмешательства
5. **Скриншоты** - сохраняются с timestamp в имени файла

## iTerm2 интеграция

### Настройка
```bash
# Запустить скрипт настройки
./scripts/setup-iterm2.sh

# Запустить Python интеграцию в iTerm2
python3 ./scripts/iterm2-integration.py
```

### Отправка скриншотов в Claude
```bash
./scripts/send-to-claude.sh [path-to-screenshot]
# Или без параметра для создания нового скриншота
./scripts/send-to-claude.sh
```

## Контакты и поддержка

Проект: GalaxyDevelopers DevSystem
Локация: /Volumes/Z7S/development/GalaxyDevelopers/DevSystem/

⚠️ **ПРАВИЛО:** Никогда не создавать новые файлы и папки без явного разрешения!