#!/bin/bash
# ==================================================
# 🔧 SERVICE MANAGER MODULE
# ==================================================
# Galaxy Orchestrator - Service Management Functions
# Version: 1.0.0
# Created: 2025-08-18
# 
# This module handles:
# - Service startup and shutdown
# - Process tracking and management
# - Service status monitoring
# - Integration with existing scripts
# ==================================================

# Ensure this script is sourced, not executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "❌ This script should be sourced, not executed directly"
    exit 1
fi

# ==================================================
# SERVICE MANAGER CONFIGURATION
# ==================================================

# Project root (parent of GALAXY_ORCHESTRATOR)
PROJECT_ROOT="$(dirname "$GALAXY_ROOT")"

# Service definitions based on our registry  
declare -A SERVICE_COMMANDS 2>/dev/null || true
SERVICE_COMMANDS[postgres]="external"
SERVICE_COMMANDS["redis"]="external"
SERVICE_COMMANDS["memory-api"]="/opt/homebrew/bin/python3 $PROJECT_ROOT/MEMORY/memory_api.py"
SERVICE_COMMANDS["backend"]="node $PROJECT_ROOT/SERVER/GalaxyDevelopersAI-backend.js"
SERVICE_COMMANDS["dev-monitoring"]="$PROJECT_ROOT/DEV_MONITORING/start_monitoring.sh"
SERVICE_COMMANDS["experience-api"]="/opt/homebrew/bin/python3 $PROJECT_ROOT/src/experience_api.py"
SERVICE_COMMANDS["voice-storage"]="/opt/homebrew/bin/python3 $PROJECT_ROOT/voice_storage.py"
SERVICE_COMMANDS["doc-system-api"]="/opt/homebrew/bin/python3 $PROJECT_ROOT/DOC_SYSTEM/api/server.py"
SERVICE_COMMANDS["doc-system-simple"]="/opt/homebrew/bin/python3 $PROJECT_ROOT/DOC_SYSTEM/api/simple_server.py"
SERVICE_COMMANDS["standards-web-dashboard"]="/opt/homebrew/bin/python3 $PROJECT_ROOT/STANDARTS_AI_DOCUMENT_SYSTEM/web_dashboard.py"
SERVICE_COMMANDS["forge-bridge"]="/opt/homebrew/bin/python3 $PROJECT_ROOT/bridge/forge_bridge.py"
SERVICE_COMMANDS["frontend-interface"]="static"

declare -A SERVICE_PORTS
SERVICE_PORTS["postgres"]="5432"
SERVICE_PORTS["redis"]="6379"
SERVICE_PORTS["memory-api"]="37778"
SERVICE_PORTS["backend"]="37777"
SERVICE_PORTS["dev-monitoring"]="8765,8766"
SERVICE_PORTS["experience-api"]="5556"
SERVICE_PORTS["voice-storage"]="5555"
SERVICE_PORTS["doc-system-api"]="8080"
SERVICE_PORTS["doc-system-simple"]="8081"
SERVICE_PORTS["standards-web-dashboard"]="8000"
SERVICE_PORTS["forge-bridge"]="8888"
SERVICE_PORTS["frontend-interface"]="3000"

declare -A SERVICE_TYPES
SERVICE_TYPES["postgres"]="external"
SERVICE_TYPES["redis"]="external"
SERVICE_TYPES["memory-api"]="python"
SERVICE_TYPES["backend"]="nodejs"
SERVICE_TYPES["dev-monitoring"]="python"
SERVICE_TYPES["experience-api"]="python"
SERVICE_TYPES["voice-storage"]="python"
SERVICE_TYPES["doc-system-api"]="python"
SERVICE_TYPES["doc-system-simple"]="python"
SERVICE_TYPES["standards-web-dashboard"]="python"
SERVICE_TYPES["forge-bridge"]="python"
SERVICE_TYPES["frontend-interface"]="static"

declare -A SERVICE_CRITICAL
SERVICE_CRITICAL["postgres"]="true"
SERVICE_CRITICAL["redis"]="true"
SERVICE_CRITICAL["memory-api"]="true"
SERVICE_CRITICAL["backend"]="true"
SERVICE_CRITICAL["dev-monitoring"]="true"
SERVICE_CRITICAL["experience-api"]="false"
SERVICE_CRITICAL["voice-storage"]="false"
SERVICE_CRITICAL["doc-system-api"]="false"
SERVICE_CRITICAL["doc-system-simple"]="false"
SERVICE_CRITICAL["standards-web-dashboard"]="false"
SERVICE_CRITICAL["forge-bridge"]="false"
SERVICE_CRITICAL["frontend-interface"]="false"

# Startup phases based on dependencies
declare -a STARTUP_PHASES=(
    "phase_1_infrastructure:postgres redis"
    "phase_2_core_memory:memory-api"
    "phase_3_core_backend:backend dev-monitoring"
    "phase_4_applications:experience-api voice-storage doc-system-api doc-system-simple standards-web-dashboard"
    "phase_5_integration:forge-bridge"
    "phase_6_frontend:frontend-interface"
)

# Shutdown phases (reverse order)
declare -a SHUTDOWN_PHASES=(
    "phase_6_frontend:frontend-interface"
    "phase_5_integration:forge-bridge"
    "phase_4_applications:experience-api voice-storage doc-system-api doc-system-simple standards-web-dashboard"
    "phase_3_core_backend:backend dev-monitoring"
    "phase_2_core_memory:memory-api"
    "phase_1_infrastructure:postgres redis"
)

# ==================================================
# PID MANAGEMENT FUNCTIONS
# ==================================================

get_pid_file() {
    local service_name="$1"
    echo "$LOGS_DIR/${service_name}.pid"
}

save_pid() {
    local service_name="$1"
    local pid="$2"
    local pid_file=$(get_pid_file "$service_name")
    echo "$pid" > "$pid_file"
    log_debug "Saved PID $pid for service $service_name"
}

get_saved_pid() {
    local service_name="$1"
    local pid_file=$(get_pid_file "$service_name")
    
    if [[ -f "$pid_file" ]]; then
        cat "$pid_file" 2>/dev/null
    else
        echo ""
    fi
}

remove_pid_file() {
    local service_name="$1"
    local pid_file=$(get_pid_file "$service_name")
    rm -f "$pid_file" 2>/dev/null
    log_debug "Removed PID file for service $service_name"
}

is_process_running() {
    local pid="$1"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        return 0  # Process is running
    else
        return 1  # Process is not running
    fi
}

# ==================================================
# SERVICE STATUS FUNCTIONS
# ==================================================

get_service_status() {
    local service_name="$1"
    local service_type="${SERVICE_TYPES[$service_name]}"
    local saved_pid=$(get_saved_pid "$service_name")
    
    case "$service_type" in
        "external")
            check_external_service_status "$service_name"
            ;;
        "static")
            echo "static"  # Frontend is served through backend
            ;;
        *)
            if [[ -n "$saved_pid" ]] && is_process_running "$saved_pid"; then
                echo "running"
            else
                echo "stopped"
            fi
            ;;
    esac
}

check_external_service_status() {
    local service_name="$1"
    local port="${SERVICE_PORTS[$service_name]}"
    
    if nc -z localhost "$port" 2>/dev/null; then
        echo "running"
    else
        echo "stopped"
    fi
}

show_services_status() {
    echo ""
    echo -e "${CYAN}📊 Service Status Report${NC}"
    echo "=============================================="
    
    local total_services=0
    local running_services=0
    local critical_down=0
    
    for service in "${!SERVICE_COMMANDS[@]}"; do
        local status=$(get_service_status "$service")
        local is_critical="${SERVICE_CRITICAL[$service]}"
        local port="${SERVICE_PORTS[$service]}"
        
        ((total_services++))
        
        # Status display
        case "$status" in
            "running")
                echo -e "  ${GREEN}✅${NC} $service (port $port) - ${GREEN}RUNNING${NC}"
                ((running_services++))
                ;;
            "stopped")
                if [[ "$is_critical" == "true" ]]; then
                    echo -e "  ${RED}❌${NC} $service (port $port) - ${RED}STOPPED (CRITICAL)${NC}"
                    ((critical_down++))
                else
                    echo -e "  ${YELLOW}⭕${NC} $service (port $port) - ${YELLOW}STOPPED${NC}"
                fi
                ;;
            "static")
                echo -e "  ${BLUE}📄${NC} $service (port $port) - ${BLUE}STATIC${NC}"
                ((running_services++))
                ;;
            *)
                echo -e "  ${PURPLE}❓${NC} $service (port $port) - ${PURPLE}UNKNOWN${NC}"
                ;;
        esac
    done
    
    echo "=============================================="
    echo -e "  Total Services: $total_services"
    echo -e "  Running: ${GREEN}$running_services${NC}"
    echo -e "  Stopped: ${RED}$((total_services - running_services))${NC}"
    if [[ $critical_down -gt 0 ]]; then
        echo -e "  ${RED}⚠️  Critical services down: $critical_down${NC}"
    fi
    echo ""
}

# ==================================================
# SERVICE CONTROL FUNCTIONS
# ==================================================

start_service() {
    local service_name="$1"
    local service_type="${SERVICE_TYPES[$service_name]}"
    local service_command="${SERVICE_COMMANDS[$service_name]}"
    local current_status=$(get_service_status "$service_name")
    
    # Skip if already running
    if [[ "$current_status" == "running" ]]; then
        log_info "Service $service_name is already running"
        return 0
    fi
    
    log_info "Starting service: $service_name"
    
    case "$service_type" in
        "external")
            start_external_service "$service_name"
            ;;
        "static")
            log_info "Frontend interface is served through backend - no separate startup needed"
            ;;
        "nodejs"|"python")
            start_managed_service "$service_name" "$service_command"
            ;;
        *)
            log_error "Unknown service type for $service_name: $service_type"
            return 1
            ;;
    esac
}

start_external_service() {
    local service_name="$1"
    
    case "$service_name" in
        "postgres")
            log_info "PostgreSQL is external - checking if running..."
            if ! check_external_service_status "postgres" | grep -q "running"; then
                log_warning "PostgreSQL not running. Please start PostgreSQL service manually."
                log_info "  macOS: brew services start postgresql"
                log_info "  Linux: sudo systemctl start postgresql"
            else
                log_success "PostgreSQL is running"
            fi
            ;;
        "redis")
            log_info "Redis is external - checking if running..."
            if ! check_external_service_status "redis" | grep -q "running"; then
                log_warning "Redis not running. Please start Redis service manually."
                log_info "  macOS: brew services start redis"
                log_info "  Linux: sudo systemctl start redis"
            else
                log_success "Redis is running"
            fi
            ;;
    esac
}

start_managed_service() {
    local service_name="$1"
    local service_command="$2"
    local service_log="$LOGS_DIR/${service_name}.log"
    
    # Special handling for services with existing start scripts
    case "$service_name" in
        "dev-monitoring")
            log_info "Starting DEV monitoring using existing start script..."
            if [[ -x "$PROJECT_ROOT/DEV_MONITORING/start_monitoring.sh" ]]; then
                (cd "$PROJECT_ROOT" && ./DEV_MONITORING/start_monitoring.sh) > "$service_log" 2>&1 &
                local pid=$!
                save_pid "$service_name" "$pid"
                log_success "Started $service_name with PID $pid"
            else
                log_error "DEV monitoring start script not found or not executable"
                return 1
            fi
            ;;
        *)
            # Standard service startup
            log_info "Executing: $service_command"
            
            # Change to project root for relative paths
            (cd "$PROJECT_ROOT" && eval "$service_command") > "$service_log" 2>&1 &
            local pid=$!
            
            save_pid "$service_name" "$pid"
            log_success "Started $service_name with PID $pid"
            
            # Brief wait to check if process started successfully
            sleep 2
            if ! is_process_running "$pid"; then
                log_error "Service $service_name failed to start - check log: $service_log"
                remove_pid_file "$service_name"
                return 1
            fi
            ;;
    esac
    
    return 0
}

stop_service() {
    local service_name="$1"
    local service_type="${SERVICE_TYPES[$service_name]}"
    local current_status=$(get_service_status "$service_name")
    
    # Skip if already stopped
    if [[ "$current_status" == "stopped" ]]; then
        log_info "Service $service_name is already stopped"
        return 0
    fi
    
    log_info "Stopping service: $service_name"
    
    case "$service_type" in
        "external")
            stop_external_service "$service_name"
            ;;
        "static")
            log_info "Frontend interface - no separate shutdown needed"
            ;;
        *)
            stop_managed_service "$service_name"
            ;;
    esac
}

stop_external_service() {
    local service_name="$1"
    log_info "External service $service_name - manual shutdown required if needed"
}

stop_managed_service() {
    local service_name="$1"
    local saved_pid=$(get_saved_pid "$service_name")
    
    if [[ -n "$saved_pid" ]]; then
        if is_process_running "$saved_pid"; then
            log_info "Terminating process $saved_pid for service $service_name"
            
            # Try graceful shutdown first
            kill -TERM "$saved_pid" 2>/dev/null
            
            # Wait up to 10 seconds for graceful shutdown
            local count=0
            while [[ $count -lt 10 ]] && is_process_running "$saved_pid"; do
                sleep 1
                ((count++))
            done
            
            # Force kill if still running
            if is_process_running "$saved_pid"; then
                log_warning "Force killing process $saved_pid for service $service_name"
                kill -KILL "$saved_pid" 2>/dev/null
                sleep 1
            fi
            
            log_success "Stopped service $service_name"
        else
            log_info "Process for $service_name was not running"
        fi
    else
        log_info "No PID file found for $service_name"
    fi
    
    remove_pid_file "$service_name"
}

restart_service() {
    local service_name="$1"
    log_info "Restarting service: $service_name"
    
    stop_service "$service_name"
    sleep 2
    start_service "$service_name"
}

# ==================================================
# PHASE-BASED STARTUP/SHUTDOWN
# ==================================================

start_services_by_phases() {
    log_info "Starting services in dependency order..."
    
    for phase_info in "${STARTUP_PHASES[@]}"; do
        local phase_name="${phase_info%%:*}"
        local services="${phase_info#*:}"
        
        log_info "=== Starting $phase_name ==="
        
        # Start services in this phase
        for service in $services; do
            start_service "$service"
            
            # Brief pause between service starts
            sleep 1
        done
        
        # Wait between phases for services to initialize
        case "$phase_name" in
            "phase_1_infrastructure")
                log_info "Waiting 10 seconds for infrastructure to initialize..."
                sleep 10
                ;;
            "phase_2_core_memory")
                log_info "Waiting 15 seconds for memory system to initialize..."
                sleep 15
                ;;
            "phase_3_core_backend")
                log_info "Waiting 20 seconds for backend and monitoring to initialize..."
                sleep 20
                ;;
            *)
                log_info "Waiting 5 seconds for services to initialize..."
                sleep 5
                ;;
        esac
    done
    
    log_success "Service startup phases completed"
}

stop_services_by_phases() {
    log_info "Stopping services in shutdown order..."
    
    for phase_info in "${SHUTDOWN_PHASES[@]}"; do
        local phase_name="${phase_info%%:*}"
        local services="${phase_info#*:}"
        
        log_info "=== Stopping $phase_name ==="
        
        # Stop services in this phase
        for service in $services; do
            stop_service "$service"
        done
        
        # Brief pause between phases
        sleep 2
    done
    
    log_success "Service shutdown phases completed"
}

# ==================================================
# STARTUP VERIFICATION
# ==================================================

verify_startup_success() {
    log_info "Verifying service startup success..."
    
    local failed_services=()
    local critical_failed=false
    
    # Check each service
    for service in "${!SERVICE_COMMANDS[@]}"; do
        local status=$(get_service_status "$service")
        local is_critical="${SERVICE_CRITICAL[$service]}"
        
        if [[ "$status" != "running" && "$status" != "static" ]]; then
            failed_services+=("$service")
            
            if [[ "$is_critical" == "true" ]]; then
                critical_failed=true
                log_error "Critical service failed to start: $service"
            else
                log_warning "Optional service failed to start: $service"
            fi
        fi
    done
    
    # Report results
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        log_success "All services started successfully!"
        return 0
    else
        log_warning "Failed services: ${failed_services[*]}"
        
        if [[ "$critical_failed" == "true" ]]; then
            log_error "Critical services failed - system may not function properly"
            return 1
        else
            log_warning "Only optional services failed - system should function normally"
            return 0
        fi
    fi
}

# ==================================================
# MODULE INITIALIZATION
# ==================================================

log_debug "Service Manager module loaded successfully"