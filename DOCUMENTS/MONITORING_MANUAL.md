# 🌌 GALAXY MONITORING SYSTEM - РУКОВОДСТВО

## 📋 ОГЛАВЛЕНИЕ
1. [Быстрый старт](#быстрый-старт)
2. [Архитектура системы](#архитектура-системы)
3. [Управление сервером](#управление-сервером)
4. [Конфигурация](#конфигурация)
5. [Панель управления](#панель-управления)
6. [API Endpoints](#api-endpoints)
7. [Мониторинг компонентов](#мониторинг-компонентов)
8. [Решение проблем](#решение-проблем)

---

## 🚀 БЫСТРЫЙ СТАРТ

### Запуск системы за 3 шага:

```bash
# 1. Запустить мониторинг
./start_monitoring.sh

# 2. Открыть дашборд (откроется автоматически)
open monitoring_dashboard.html

# 3. Проверить статус
./monitoring_status.sh
```

### Остановка системы:
```bash
./stop_monitoring.sh
```

---

## 🏗️ АРХИТЕКТУРА СИСТЕМЫ

### Компоненты:

```
┌─────────────────────────────────────────────┐
│           GALAXY MONITORING SYSTEM          │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐    ┌──────────────┐      │
│  │  WebSocket   │    │   REST API   │      │
│  │   :8765      │    │    :8766     │      │
│  └──────────────┘    └──────────────┘      │
│          │                   │              │
│          └───────┬───────────┘              │
│                  │                          │
│  ┌───────────────────────────────────┐     │
│  │      MONITORING CORE              │     │
│  ├───────────────────────────────────┤     │
│  │ • File Observer                   │     │
│  │ • Syntax Checker                  │     │
│  │ • Security Scanner                │     │
│  │ • Compliance Validator            │     │
│  │ • Agent Integration               │     │
│  └───────────────────────────────────┘     │
│                                             │
└─────────────────────────────────────────────┘
```

### Файловая структура:

```
/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/
├── monitoring_server_fixed.py     # Основной сервер
├── monitoring_config.json         # Конфигурация
├── monitoring_dashboard.html      # Веб-дашборд
├── interface/
│   ├── index.html                # Главная панель
│   └── js/
│       └── monitoring-module.js  # Модуль для панели
├── start_monitoring.sh           # Скрипт запуска
├── stop_monitoring.sh            # Скрипт остановки
├── restart_monitoring.sh         # Скрипт перезапуска
├── monitoring_status.sh          # Проверка статуса
└── logs/
    └── monitoring.log            # Логи системы
```

---

## 🎮 УПРАВЛЕНИЕ СЕРВЕРОМ

### ЗАПУСК
```bash
./start_monitoring.sh
```
**Что происходит:**
- Проверка зависимостей
- Установка недостающих пакетов
- Запуск WebSocket сервера (порт 8765)
- Запуск REST API (порт 8766)
- Открытие дашборда в браузере

### ОСТАНОВКА
```bash
./stop_monitoring.sh
```
**Что происходит:**
- Остановка всех процессов
- Освобождение портов
- Очистка PID файла

### ПЕРЕЗАПУСК
```bash
./restart_monitoring.sh
```

### ПРОВЕРКА СТАТУСА
```bash
./monitoring_status.sh
```
**Показывает:**
- Статус WebSocket сервера
- Статус REST API
- Количество подключений
- Активные компоненты
- Последние логи

### ПРОСМОТР ЛОГОВ
```bash
# Последние 50 строк
tail -n 50 logs/monitoring.log

# В реальном времени
tail -f logs/monitoring.log

# Поиск ошибок
grep ERROR logs/monitoring.log
```

---

## ⚙️ КОНФИГУРАЦИЯ

### Основной файл: `monitoring_config.json`

#### Ключевые настройки:

**1. WebSocket сервер:**
```json
"websocket": {
    "host": "localhost",
    "port": 8765,
    "ping_interval": 20,    // Интервал ping (сек)
    "max_connections": 100   // Макс. подключений
}
```

**2. REST API:**
```json
"api": {
    "host": "localhost",
    "port": 8766,
    "cors_enabled": true,
    "rate_limit": {
        "enabled": true,
        "requests_per_minute": 60
    }
}
```

**3. File Watcher:**
```json
"file_watcher": {
    "enabled": true,
    "paths": [
        "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/",
        "/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/"
    ],
    "ignored_patterns": [".git", "__pycache__", "*.pyc"]
}
```

**4. Проверки безопасности:**
```json
"security_scan": {
    "enabled": true,
    "interval_seconds": 600,      // Каждые 10 минут
    "severity_threshold": "MEDIUM"
}
```

**5. Compliance стандарты:**
```json
"compliance": {
    "standards": {
        "ISO27001": {"enabled": true, "threshold": 80},
        "ITIL4": {"enabled": true, "threshold": 75},
        "COBIT": {"enabled": true, "threshold": 70}
    }
}
```

### Применение изменений:
После изменения конфигурации:
```bash
./restart_monitoring.sh
```

---

## 🖥️ ПАНЕЛЬ УПРАВЛЕНИЯ

### Веб-интерфейсы:

**1. Основной дашборд:**
```
http://localhost:8766/monitoring_dashboard.html
```

**2. Интегрированная панель:**
```
file:///Volumes/Z7S/development/GalaxyDevelopers/DevSystem/interface/index.html
```

### Функции панели:

#### В правом верхнем углу появится панель мониторинга:

**Статусы компонентов:**
- 🟢 Зеленый - работает
- 🔵 Синий - выполняется проверка
- 🔴 Красный - ошибка
- ⚫ Серый - отключено

**Действия:**
- **Полное сканирование** - запуск всех проверок
- **Проверка синтаксиса** - поиск ошибок в коде
- **Сканирование безопасности** - поиск уязвимостей
- **Проверка Compliance** - соответствие стандартам
- **Перезапуск сервера** - перезапуск всех компонентов

**Метрики в реальном времени:**
- Изменения файлов
- Синтаксические ошибки
- Уязвимости безопасности
- WebSocket подключения

---

## 🔌 API ENDPOINTS

### REST API доступен на: `http://localhost:8766`

#### Основные endpoints:

**Статус системы:**
```bash
curl http://localhost:8766/api/monitoring/status
```

**Изменения файлов:**
```bash
curl http://localhost:8766/api/monitoring/file-changes
```

**Проверка синтаксиса:**
```bash
curl http://localhost:8766/api/monitoring/syntax-check
```

**Сканирование безопасности:**
```bash
curl http://localhost:8766/api/monitoring/security-scan
```

**Проверка соответствия:**
```bash
# ISO 27001
curl http://localhost:8766/api/monitoring/compliance/ISO27001

# ITIL 4
curl http://localhost:8766/api/monitoring/compliance/ITIL4

# COBIT
curl http://localhost:8766/api/monitoring/compliance/COBIT
```

**Prometheus метрики:**
```bash
curl http://localhost:8766/api/monitoring/metrics
```

**Интеграционные тесты:**
```bash
curl http://localhost:8766/api/monitoring/integration-test
```

### WebSocket подключение:
```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Получено:', data);
};

// Отправка ping
ws.send(JSON.stringify({type: 'ping'}));
```

---

## 📊 МОНИТОРИНГ КОМПОНЕНТОВ

### File Observer
**Что делает:** Отслеживает изменения файлов в указанных директориях

**Настройка путей:**
Редактировать в `monitoring_config.json`:
```json
"paths": [
    "/путь/к/директории1",
    "/путь/к/директории2"
]
```

### Syntax Checker
**Что делает:** Проверяет синтаксис Python и JavaScript файлов

**Поддерживаемые языки:**
- Python (.py)
- JavaScript (.js)
- TypeScript (.ts)

### Security Scanner
**Что делает:** Ищет уязвимости в коде

**Проверки:**
- Hardcoded пароли и ключи
- SQL инъекции
- XSS уязвимости
- Небезопасные функции

### Compliance Validator
**Что делает:** Проверяет соответствие стандартам

**Стандарты:**
- ISO 27001 - Информационная безопасность
- ITIL 4 - Управление IT-сервисами
- COBIT - Управление и аудит IT

---

## 🔧 РЕШЕНИЕ ПРОБЛЕМ

### Сервер не запускается

**1. Порты заняты:**
```bash
# Проверить занятые порты
lsof -i :8765
lsof -i :8766

# Освободить порты
./stop_monitoring.sh
```

**2. Отсутствуют зависимости:**
```bash
pip3 install aiohttp aiohttp-cors websockets watchdog prometheus-client bandit pylint
```

### WebSocket не подключается

**1. Проверить статус:**
```bash
./monitoring_status.sh
```

**2. Проверить логи:**
```bash
grep "WebSocket" logs/monitoring.log
```

**3. Перезапустить:**
```bash
./restart_monitoring.sh
```

### File Observer не работает

**1. Проверить права доступа:**
```bash
ls -la /путь/к/директории
```

**2. Проверить конфигурацию:**
```bash
cat monitoring_config.json | grep -A5 "file_watcher"
```

### Высокая нагрузка на CPU

**1. Уменьшить частоту проверок:**
В `monitoring_config.json`:
```json
"periodic_checks": {
    "interval_seconds": 60  // Увеличить интервал
}
```

**2. Ограничить количество файлов:**
Добавить больше паттернов в `ignored_patterns`

---

## 🚨 АВТОЗАПУСК

### macOS (launchd):

**1. Создать plist файл:**
```bash
cat > ~/Library/LaunchAgents/com.galaxy.monitoring.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.galaxy.monitoring</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/start_monitoring.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/Volumes/Z7S/development/GalaxyDevelopers/DevSystem</string>
</dict>
</plist>
EOF
```

**2. Загрузить сервис:**
```bash
launchctl load ~/Library/LaunchAgents/com.galaxy.monitoring.plist
```

**3. Управление:**
```bash
# Остановить
launchctl unload ~/Library/LaunchAgents/com.galaxy.monitoring.plist

# Запустить
launchctl load ~/Library/LaunchAgents/com.galaxy.monitoring.plist
```

---

## 📞 ПОДДЕРЖКА

**Логи:** `logs/monitoring.log`
**Конфигурация:** `monitoring_config.json`
**Статус:** `./monitoring_status.sh`

При возникновении проблем:
1. Проверьте статус: `./monitoring_status.sh`
2. Посмотрите логи: `tail -n 100 logs/monitoring.log`
3. Перезапустите: `./restart_monitoring.sh`

---

## 🎯 БЫСТРЫЕ КОМАНДЫ

```bash
# Запуск
./start_monitoring.sh

# Остановка
./stop_monitoring.sh

# Перезапуск
./restart_monitoring.sh

# Статус
./monitoring_status.sh

# Логи в реальном времени
tail -f logs/monitoring.log

# Открыть дашборд
open monitoring_dashboard.html

# Тестирование API
curl http://localhost:8766/api/monitoring/status | python3 -m json.tool
```

---

*Galaxy Monitoring System v2.1 - Real-time System Monitoring*