#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- CONFIGURATION ---
LOGS_DIR="GALAXY_ORCHESTRATOR/logs"

# --- HELPER FUNCTIONS ---
start_service() {
    local service_name=$1
    local command=$2
    local log_file=$3
    local pid_file=$4

    echo "Starting $service_name..."
    eval "$command" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    echo "$service_name started with PID: $pid"
}

# --- MAIN SCRIPT ---
echo " GALAXY DEVELOPERS SYSTEM - AUTOMATIC STARTUP"
echo "================================================"

# Create logs directory
mkdir -p $LOGS_DIR

# Make all scripts executable
chmod +x install-dependencies.sh setup-databases.sh health-check.sh galaxy-stop.sh galaxy-status.sh

# --- PHASE 1: INFRASTRUCTURE ---
echo "
Phase 1: Infrastructure Setup"
./install-dependencies.sh
./setup-databases.sh

# --- PHASE 2: CORE SERVICES ---
echo "
Phase 2: Core Services Launch"
start_service "Memory API" "python3 MEMORY/memory_api.py" "$LOGS_DIR/memory-api.log" "$LOGS_DIR/memory-api.pid"
start_service "Backend API" "node SERVER/GalaxyDevelopersAI-backend.js" "$LOGS_DIR/backend.log" "$LOGS_DIR/backend.pid"
start_service "Experience API" "python3 src/experience_api.py" "$LOGS_DIR/experience-api.log" "$LOGS_DIR/experience-api.pid"

# --- PHASE 3: MONITORING & FRONTEND ---
echo "
Phase 3: Monitoring & Frontend"
start_service "Monitoring Server" "python3 DEV_MONITORING/monitoring_server.py" "$LOGS_DIR/dev-monitoring.log" "$LOGS_DIR/dev-monitoring.pid"
start_service "Frontend Interface" "serve -s INTERFACE -l 3000" "$LOGS_DIR/frontend.log" "$LOGS_DIR/frontend.pid"

# --- PHASE 4: INTEGRATIONS ---
echo "
Phase 4: Integration Activation"
start_service "Claude Bridge" "python3 superclaude-bridge.py" "$LOGS_DIR/superclaude-bridge.log" "$LOGS_DIR/superclaude-bridge.pid"
start_service "FORGE Integration" "python3 bridge/forge_bridge.py" "$LOGS_DIR/forge_bridge.log" "$LOGS_DIR/forge_bridge.pid"

# --- FINAL HEALTH CHECK ---
echo "
Waiting for services to start..."
sleep 10 # Give services time to start
./health-check.sh

echo "
 SYSTEM FULLY OPERATIONAL!"

# --- OPEN FRONTEND ---
open http://localhost:3000

# --- MANAGEMENT COMMANDS INFO ---
echo "
Management Commands:"
echo "./galaxy-stop.sh     - Stop all services"
echo "./galaxy-status.sh   - Check system status"
echo "./galaxy-logs.sh     - View system logs"