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

echo "--- RUNNING HEALTH CHECKS ---"

check_service "Backend API" "http://localhost:37777/api/status"
check_service "Memory API" "http://localhost:37778/health"
check_service "Monitoring Server" "http://localhost:8766/api/monitoring/status"

# The prompt does not specify a health check endpoint for the Experience API.
# Assuming '/health' endpoint.
check_service "Experience API" "http://localhost:5556/health"

# Check if frontend port is open
echo -n "Checking Frontend Interface... "
if nc -z localhost 3000; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

echo "--- HEALTH CHECKS COMPLETE ---"
