#!/bin/bash

LOGS_DIR="GALAXY_ORCHESTRATOR/logs"

# Function to check service status
check_status() {
    local service_name=$1
    local pid_file=$2
    local port=$3

    echo -n "$service_name (Port: $port): "

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            if nc -z localhost $port; then
                echo "✅ RUNNING"
            else
                echo "❌ RUNNING (Port not listening)"
            fi
        else
            echo "❌ STOPPED (PID file exists but process not running)"
        fi
    else
        echo "❌ STOPPED (No PID file)"
    fi
}

echo "--- GALAXY DEVELOPERS SYSTEM STATUS ---"

check_status "Backend API" "$LOGS_DIR/backend.pid" 37777
check_status "Memory API" "$LOGS_DIR/memory-api.pid" 37778
check_status "Monitoring Server" "$LOGS_DIR/dev-monitoring.pid" 8766
check_status "Experience API" "$LOGS_DIR/experience-api.pid" 5556
check_status "Frontend Interface" "$LOGS_DIR/frontend.pid" 3000
check_status "Claude Bridge" "$LOGS_DIR/superclaude-bridge.pid" 8001 # Assuming port 8001 for Claude Bridge
check_status "FORGE Integration" "$LOGS_DIR/forge_bridge.pid" 8002 # Assuming port 8002 for FORGE

echo "-------------------------------------"
