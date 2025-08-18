#!/bin/bash

# GALAXY MONITORING AUTOSTART
# Автозапуск мониторинга при старте системы

echo "🚀 GALAXY MONITORING AUTOSTART"

# Определяем платформу
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    PLIST_PATH="$HOME/Library/LaunchAgents/com.galaxy.monitoring.plist"
    MONITORING_PATH="/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/DEV_MONITORING"
    
    echo "📝 Создание LaunchAgent для macOS..."
    
    # Создаем plist файл
    cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.galaxy.monitoring</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$MONITORING_PATH/start_monitoring.sh</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$MONITORING_PATH</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>$MONITORING_PATH/logs/autostart.log</string>
    
    <key>StandardErrorPath</key>
    <string>$MONITORING_PATH/logs/autostart_error.log</string>
    
    <key>StartInterval</key>
    <integer>30</integer>
    
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF
    
    # Устанавливаем права
    chmod 644 "$PLIST_PATH"
    
    # Загружаем сервис
    launchctl unload "$PLIST_PATH" 2>/dev/null
    launchctl load "$PLIST_PATH"
    
    echo "✅ LaunchAgent установлен: $PLIST_PATH"
    echo ""
    echo "📌 Команды управления:"
    echo "   Остановить автозапуск:  launchctl unload $PLIST_PATH"
    echo "   Включить автозапуск:    launchctl load $PLIST_PATH"
    echo "   Проверить статус:       launchctl list | grep galaxy"
    echo ""
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux с systemd
    SERVICE_PATH="/etc/systemd/system/galaxy-monitoring.service"
    MONITORING_PATH="/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/DEV_MONITORING"
    
    echo "📝 Создание systemd сервиса для Linux..."
    
    # Создаем service файл (требует sudo)
    sudo tee "$SERVICE_PATH" > /dev/null << EOF
[Unit]
Description=Galaxy Monitoring System
After=network.target

[Service]
Type=forking
WorkingDirectory=$MONITORING_PATH
ExecStart=/bin/bash $MONITORING_PATH/start_monitoring.sh
ExecStop=/bin/bash $MONITORING_PATH/stop_monitoring.sh
Restart=always
RestartSec=10
User=$USER

[Install]
WantedBy=multi-user.target
EOF
    
    # Перезагружаем systemd и включаем сервис
    sudo systemctl daemon-reload
    sudo systemctl enable galaxy-monitoring.service
    sudo systemctl start galaxy-monitoring.service
    
    echo "✅ Systemd сервис установлен: $SERVICE_PATH"
    echo ""
    echo "📌 Команды управления:"
    echo "   Остановить:  sudo systemctl stop galaxy-monitoring"
    echo "   Запустить:   sudo systemctl start galaxy-monitoring"
    echo "   Статус:      sudo systemctl status galaxy-monitoring"
    echo "   Отключить:   sudo systemctl disable galaxy-monitoring"
    echo ""
else
    echo "❌ Неподдерживаемая операционная система: $OSTYPE"
    exit 1
fi

echo "🎯 Автозапуск настроен!"
echo "   Мониторинг будет автоматически запускаться при старте системы"
echo "   и перезапускаться в случае сбоя"