#!/bin/bash

# GALAXY MONITORING - AUTOSTART INSTALLER
# Установка автозапуска системы мониторинга

echo "╔════════════════════════════════════════╗"
echo "║    GALAXY MONITORING AUTOSTART         ║"
echo "║    Installing launch daemon...         ║"
echo "╚════════════════════════════════════════╝"
echo ""

PLIST_FILE="com.galaxy.monitoring.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
TARGET_PLIST="$LAUNCH_AGENTS_DIR/$PLIST_FILE"

# Создаем директорию если её нет
mkdir -p "$LAUNCH_AGENTS_DIR"

# Копируем plist файл
echo "📁 Копирование plist файла..."
cp "$PLIST_FILE" "$TARGET_PLIST"

# Устанавливаем правильные права
chmod 644 "$TARGET_PLIST"

# Выгружаем если уже загружен
echo "🔄 Проверка существующего сервиса..."
launchctl unload "$TARGET_PLIST" 2>/dev/null

# Загружаем сервис
echo "🚀 Загрузка сервиса..."
launchctl load "$TARGET_PLIST"

# Проверяем статус
echo ""
echo "✅ Автозапуск установлен!"
echo ""
echo "📋 Управление автозапуском:"
echo "   Остановить:  launchctl unload $TARGET_PLIST"
echo "   Запустить:   launchctl load $TARGET_PLIST"
echo "   Статус:      launchctl list | grep galaxy"
echo "   Удалить:     launchctl unload $TARGET_PLIST && rm $TARGET_PLIST"
echo ""
echo "📝 Логи автозапуска:"
echo "   stdout: logs/launchd.out.log"
echo "   stderr: logs/launchd.err.log"
echo ""

# Проверяем что сервис загружен
if launchctl list | grep -q "com.galaxy.monitoring"; then
    echo "✅ Сервис успешно загружен и будет запускаться автоматически"
else
    echo "⚠️  Сервис не найден в списке загруженных"
fi