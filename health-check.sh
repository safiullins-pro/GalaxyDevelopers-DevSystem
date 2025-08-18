#!/bin/bash

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    echo -n "Checking $service_name... "
    if curl -s --head --request GET -m 5 $url | grep "200 OK" > /dev/null; then
        echo "✅ OK"
    else
        echo "❌ FAILED"
    fi
}

# Function to check port
check_port() {
    local service_name=$1
    local port=$2
    echo -n "Checking $service_name... "
    if nc -z localhost $port; then
        echo "✅ OK"
    else
        echo "❌ FAILED"
    fi
}

echo "--- RUNNING HEALTH CHECKS ---"

check_service "Backend API" "http://localhost:37777/api/status"
check_service "Memory API" "http://localhost:37778/health"
check_service "Monitoring Server (API)" "http://localhost:8766/api/monitoring/status"
check_port "Monitoring Server (WebSocket)" 8765
check_service "Experience API" "http://localhost:5556/api/health"
check_port "Frontend Interface" 3000

echo "--- HEALTH CHECKS COMPLETE ---"