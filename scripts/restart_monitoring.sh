#!/bin/bash

# GALAXY MONITORING - RESTART SCRIPT
# Скрипт перезапуска системы мониторинга

echo "╔════════════════════════════════════════╗"
echo "║    GALAXY MONITORING SYSTEM            ║"
echo "║    Restarting all components...        ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Останавливаем
./stop_monitoring.sh

echo ""
echo "⏳ Ожидание 2 секунды..."
sleep 2

echo ""
# Запускаем
./start_monitoring.sh