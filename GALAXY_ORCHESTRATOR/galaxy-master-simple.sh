#!/bin/bash
# ==================================================
# 🎯 GALAXY ORCHESTRATOR - Simple Version
# ==================================================
# Version: 1.0.0
# Created: 2025-08-18
# DevOps Infrastructure Orchestration Specialist
# 
# USAGE:
#   ./galaxy-master-simple.sh start    # Start all services
#   ./galaxy-master-simple.sh stop     # Stop all services  
#   ./galaxy-master-simple.sh status   # Show system status
# ==================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
GALAXY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$GALAXY_ROOT")"
LOGS_DIR="$GALAXY_ROOT/logs"
mkdir -p "$LOGS_DIR"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✅]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[⚠️]${NC} $*"
}

log_error() {
    echo -e "${RED}[❌]${NC} $*"
}

# ==================================================
# SERVICE DEFINITIONS
# ==================================================

start_all_services() {
    log_info "🚀 Starting Galaxy Developer System..."
    
    # Phase 1: Infrastructure (External services check)
    log_info "=== Phase 1: Infrastructure Check ==="
    check_postgres
    check_redis
    sleep 5
    
    # Phase 2: Core Memory
    log_info "=== Phase 2: Core Memory ==="
    start_memory_api
    sleep 10
    
    # Phase 3: Backend & Monitoring  
    log_info "=== Phase 3: Backend & Monitoring ==="
    start_backend &
    start_monitoring &
    wait
    sleep 15
    
    # Phase 4: Applications
    log_info "=== Phase 4: Application Services ==="
    start_experience_api &
    start_voice_storage &
    start_doc_services &
    wait
    sleep 5
    
    log_success "🎉 Galaxy System startup completed!"
    show_startup_summary
}

stop_all_services() {
    log_info "🛑 Stopping Galaxy Developer System..."
    
    # Stop all Python and Node processes related to our services
    log_info "Stopping all Galaxy services..."
    
    # Stop specific services by PID if available
    for service in backend memory-api experience-api voice-storage dev-monitoring; do
        if [[ -f "$LOGS_DIR/${service}.pid" ]]; then
            local pid=$(cat "$LOGS_DIR/${service}.pid")
            if kill -0 "$pid" 2>/dev/null; then
                log_info "Stopping $service (PID: $pid)"
                kill -TERM "$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null
            fi
            rm -f "$LOGS_DIR/${service}.pid"
        fi
    done
    
    # Clean shutdown
    sleep 3
    log_success "🎯 Galaxy System shutdown completed!"
}

# ==================================================
# INDIVIDUAL SERVICE FUNCTIONS
# ==================================================

check_postgres() {
    if nc -z localhost 5432 2>/dev/null; then
        log_success "PostgreSQL is running (port 5432)"
    else
        log_warning "PostgreSQL not running - please start: brew services start postgresql"
    fi
}

check_redis() {
    if nc -z localhost 6379 2>/dev/null; then
        log_success "Redis is running (port 6379)"
    else
        log_warning "Redis not running - please start: brew services start redis"
    fi
}

start_memory_api() {
    log_info "Starting Memory API..."
    cd "$PROJECT_ROOT"
    /opt/homebrew/bin/python3 MEMORY/memory_api.py > "$LOGS_DIR/memory-api.log" 2>&1 &
    echo $! > "$LOGS_DIR/memory-api.pid"
    log_success "Memory API started (PID: $!)"
}

start_backend() {
    log_info "Starting Backend API..."
    cd "$PROJECT_ROOT"
    node SERVER/GalaxyDevelopersAI-backend.js > "$LOGS_DIR/backend.log" 2>&1 &
    echo $! > "$LOGS_DIR/backend.pid"
    log_success "Backend API started (PID: $!)"
}

start_monitoring() {
    log_info "Starting DEV Monitoring..."
    cd "$PROJECT_ROOT"
    if [[ -x "DEV_MONITORING/start_monitoring.sh" ]]; then
        ./DEV_MONITORING/start_monitoring.sh > "$LOGS_DIR/dev-monitoring.log" 2>&1 &
        echo $! > "$LOGS_DIR/dev-monitoring.pid"
        log_success "DEV Monitoring started (PID: $!)"
    else
        log_warning "DEV Monitoring start script not found"
    fi
}

start_experience_api() {
    log_info "Starting Experience API..."
    cd "$PROJECT_ROOT"
    /opt/homebrew/bin/python3 src/experience_api.py > "$LOGS_DIR/experience-api.log" 2>&1 &
    echo $! > "$LOGS_DIR/experience-api.pid"
    log_success "Experience API started (PID: $!)"
}

start_voice_storage() {
    log_info "Starting Voice Storage..."
    cd "$PROJECT_ROOT"
    /opt/homebrew/bin/python3 voice_storage.py > "$LOGS_DIR/voice-storage.log" 2>&1 &
    echo $! > "$LOGS_DIR/voice-storage.pid"
    log_success "Voice Storage started (PID: $!)"
}

start_doc_services() {
    log_info "Starting Documentation services..."
    cd "$PROJECT_ROOT"
    
    # DOC_SYSTEM API
    if [[ -f "DOC_SYSTEM/api/server.py" ]]; then
        /opt/homebrew/bin/python3 DOC_SYSTEM/api/server.py > "$LOGS_DIR/doc-system-api.log" 2>&1 &
        echo $! > "$LOGS_DIR/doc-system-api.pid"
        log_success "DOC System API started (PID: $!)"
    fi
    
    # Standards Dashboard  
    if [[ -f "STANDARTS_AI_DOCUMENT_SYSTEM/web_dashboard.py" ]]; then
        /opt/homebrew/bin/python3 STANDARTS_AI_DOCUMENT_SYSTEM/web_dashboard.py > "$LOGS_DIR/standards-dashboard.log" 2>&1 &
        echo $! > "$LOGS_DIR/standards-dashboard.pid" 
        log_success "Standards Dashboard started (PID: $!)"
    fi
}

# ==================================================
# STATUS FUNCTIONS
# ==================================================

show_system_status() {
    log_info "📊 Galaxy System Status Report"
    echo "=============================================="
    
    check_service_status "PostgreSQL" 5432
    check_service_status "Redis" 6379
    check_service_status "Memory API" 37778
    check_service_status "Backend API" 37777
    check_service_status "Experience API" 5556
    check_service_status "Voice Storage" 5555
    check_service_status "DEV Monitoring (HTTP)" 8766
    check_service_status "DEV Monitoring (WS)" 8765
    check_service_status "DOC System API" 8080
    check_service_status "Standards Dashboard" 8000
    
    echo "=============================================="
    echo -e "  ${CYAN}Logs Directory:${NC} $LOGS_DIR"
    echo -e "  ${CYAN}Config Directory:${NC} $GALAXY_ROOT/config"
    echo ""
}

check_service_status() {
    local service_name="$1"
    local port="$2"
    
    if nc -z localhost "$port" 2>/dev/null; then
        echo -e "  ${GREEN}✅${NC} $service_name (port $port) - ${GREEN}RUNNING${NC}"
    else
        echo -e "  ${RED}❌${NC} $service_name (port $port) - ${RED}STOPPED${NC}"
    fi
}

show_startup_summary() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎉 GALAXY SYSTEM READY! 🎉                ║${NC}"
    echo -e "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║  🌐 Frontend Interface:  http://localhost:3000               ║${NC}"
    echo -e "${GREEN}║  🚀 Backend API:         http://localhost:37777              ║${NC}"
    echo -e "${GREEN}║  🧠 Memory API:          http://localhost:37778              ║${NC}"
    echo -e "${GREEN}║  📊 Monitoring:          http://localhost:8766               ║${NC}"
    echo -e "${GREEN}║  🔗 Experience API:      http://localhost:5556               ║${NC}"
    echo -e "${GREEN}║  🎵 Voice Storage:       http://localhost:5555               ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║  📝 Logs: $LOGS_DIR${NC}"
    echo -e "${GREEN}║  🔧 Status: ./galaxy-master-simple.sh status                ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

show_usage() {
    echo ""
    echo -e "${CYAN}🎯 GALAXY ORCHESTRATOR - Simple Version${NC}"
    echo ""
    echo -e "${GREEN}USAGE:${NC}"
    echo "  $0 start     - Start all Galaxy services"
    echo "  $0 stop      - Stop all Galaxy services"
    echo "  $0 status    - Show current system status"
    echo ""
    echo -e "${GREEN}EXAMPLES:${NC}"
    echo "  $0 start     # Start entire system"
    echo "  $0 status    # Check what's running"
    echo ""
    echo -e "${GREEN}SERVICES MANAGED:${NC}"
    echo "  • Backend API (Node.js) - port 37777"
    echo "  • Memory API (Python) - port 37778"
    echo "  • Experience API (Python) - port 5556"
    echo "  • Voice Storage (Python) - port 5555"
    echo "  • DEV Monitoring (Python) - ports 8765,8766"
    echo "  • Documentation Services - ports 8080,8000"
    echo ""
}

# ==================================================
# MAIN EXECUTION
# ==================================================

main() {
    case "${1:-}" in
        start)
            start_all_services
            ;;
        stop)
            stop_all_services
            ;;
        status)
            show_system_status
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            echo -e "${RED}❌ Unknown command: ${1:-}${NC}"
            show_usage
            exit 1
            ;;
    esac
}

# Ensure we're in the right directory
cd "$GALAXY_ROOT"

# Run main function
main "$@"