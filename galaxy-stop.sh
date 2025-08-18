#!/bin/bash

LOGS_DIR="GALAXY_ORCHESTRATOR/logs"

echo "--- STOPPING GALAXY DEVELOPERS SYSTEM ---"

# Find and kill all processes managed by PID files
for pid_file in $LOGS_DIR/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        service_name=$(basename "$pid_file" .pid)
        echo -n "Stopping $service_name (PID: $pid)... "
        if ps -p $pid > /dev/null; then
            kill $pid
            echo "✅ STOPPED"
        else
            echo "⚠️ ALREADY STOPPED"
        fi
        rm -f "$pid_file"
    fi
done

echo "--- ALL SERVICES STOPPED ---"
