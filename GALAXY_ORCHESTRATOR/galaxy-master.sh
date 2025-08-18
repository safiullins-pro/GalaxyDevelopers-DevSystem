#!/bin/bash
# ==================================================
# 🎯 GALAXY ORCHESTRATOR - Single Command System Control
# ==================================================
# Version: 1.0.0
# Created: 2025-08-18
# DevOps Infrastructure Orchestration Specialist
# 
# USAGE:
#   ./galaxy-master.sh start    # Start all services
#   ./galaxy-master.sh stop     # Stop all services  
#   ./galaxy-master.sh restart  # Restart all services
#   ./galaxy-master.sh status   # Show system status
#   ./galaxy-master.sh health   # Run health checks
# ==================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ==================================================
# GALAXY ORCHESTRATOR CONFIGURATION
# ==================================================

GALAXY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$GALAXY_ROOT/config"
MODULES_DIR="$GALAXY_ROOT/modules"
SERVICES_DIR="$GALAXY_ROOT/services"
LOGS_DIR="$GALAXY_ROOT/logs"

# Ensure directories exist
mkdir -p "$LOGS_DIR"

# Master log file
MASTER_LOG="$LOGS_DIR/galaxy-master.log"

# ==================================================
# UTILITY FUNCTIONS
# ==================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$MASTER_LOG"
}

log_info() {
    log "INFO" "$@"
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    log "SUCCESS" "$@"
    echo -e "${GREEN}[✅]${NC} $*"
}

log_warning() {
    log "WARNING" "$@"
    echo -e "${YELLOW}[⚠️]${NC} $*"
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}[❌]${NC} $*"
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        log "DEBUG" "$@"
        echo -e "${PURPLE}[DEBUG]${NC} $*"
    fi
}

# ==================================================
# CONFIGURATION LOADING
# ==================================================

load_service_config() {
    if [[ ! -f "$CONFIG_DIR/services.yaml" ]]; then
        log_error "Services configuration not found: $CONFIG_DIR/services.yaml"
        exit 1
    fi
    log_debug "Loaded services configuration"
}

load_dependencies_config() {
    if [[ ! -f "$CONFIG_DIR/dependencies.yaml" ]]; then
        log_error "Dependencies configuration not found: $CONFIG_DIR/dependencies.yaml"
        exit 1
    fi
    log_debug "Loaded dependencies configuration"
}

load_ports_config() {
    if [[ ! -f "$CONFIG_DIR/ports.yaml" ]]; then
        log_error "Ports configuration not found: $CONFIG_DIR/ports.yaml"
        exit 1
    fi
    log_debug "Loaded ports configuration"
}

# ==================================================
# SERVICE MANAGEMENT FUNCTIONS
# ==================================================

source_modules() {
    # Load all orchestration modules
    local modules=(
        "service-manager.sh"
        "health-monitor.sh" 
        "dependency-resolver.sh"
        "port-manager.sh"
    )
    
    for module in "${modules[@]}"; do
        local module_path="$MODULES_DIR/$module"
        if [[ -f "$module_path" ]]; then
            source "$module_path"
            log_debug "Loaded module: $module"
        else
            log_warning "Module not found: $module_path"
        fi
    done
}

# ==================================================
# MAIN ORCHESTRATION FUNCTIONS
# ==================================================

start_all_services() {
    log_info "🚀 Starting Galaxy Developer System..."
    log_info "Timestamp: $(date)"
    
    # Load configurations
    load_service_config
    load_dependencies_config
    load_ports_config
    
    # Check prerequisites
    log_info "Checking system prerequisites..."
    check_system_prerequisites
    
    # Start services in dependency order
    log_info "Starting services in dependency order..."
    start_services_by_phases
    
    # Verify all services are running
    log_info "Verifying service startup..."
    verify_startup_success
    
    log_success "🎉 Galaxy System startup completed!"
    show_startup_summary
}

stop_all_services() {
    log_info "🛑 Stopping Galaxy Developer System..."
    log_info "Timestamp: $(date)"
    
    # Load configurations
    load_service_config
    load_dependencies_config
    
    # Stop services in reverse dependency order
    log_info "Stopping services in shutdown order..."
    stop_services_by_phases
    
    # Clean up PIDs and temporary files
    log_info "Cleaning up process files..."
    cleanup_process_files
    
    log_success "🎯 Galaxy System shutdown completed!"
    show_shutdown_summary
}

restart_all_services() {
    log_info "🔄 Restarting Galaxy Developer System..."
    
    stop_all_services
    sleep 5  # Brief pause between stop and start
    start_all_services
    
    log_success "🔄 Galaxy System restart completed!"
}

show_system_status() {
    log_info "📊 Galaxy System Status Report"
    log_info "Timestamp: $(date)"
    log_info "=========================================="
    
    # Load configuration
    load_service_config
    
    # Show service status
    show_services_status
    
    # Show port usage
    show_port_status
    
    # Show system resources
    show_resource_usage
    
    log_info "=========================================="
}

run_health_checks() {
    log_info "💓 Running Galaxy System Health Checks..."
    log_info "Timestamp: $(date)"
    
    # Load configuration
    load_service_config
    load_ports_config
    
    # Run comprehensive health checks
    run_comprehensive_health_checks
    
    # Show health summary
    show_health_summary
}

# ==================================================
# SYSTEM CHECKS
# ==================================================

check_system_prerequisites() {
    local errors=0
    
    # Check for required commands
    local required_commands=("node" "python3" "curl" "pgrep" "pkill")
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Required command not found: $cmd"
            ((errors++))
        fi
    done
    
    # Check for required directories
    local project_root="$(dirname "$GALAXY_ROOT")"
    local required_dirs=("SERVER" "MEMORY" "src" "DEV_MONITORING")
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$project_root/$dir" ]]; then
            log_error "Required directory not found: $project_root/$dir"
            ((errors++))
        fi
    done
    
    # Check for critical files
    local critical_files=(
        "$project_root/SERVER/GalaxyDevelopersAI-backend.js"
        "$project_root/MEMORY/memory_api.py"
        "$project_root/src/experience_api.py"
    )
    
    for file in "${critical_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Critical file not found: $file"
            ((errors++))
        fi
    done
    
    if [[ $errors -gt 0 ]]; then
        log_error "System prerequisites check failed with $errors errors"
        exit 1
    fi
    
    log_success "System prerequisites check passed"
}

# ==================================================
# PLACEHOLDER FUNCTIONS (To be implemented in modules)
# ==================================================

start_services_by_phases() {
    log_info "🔧 Service startup will be implemented in service-manager.sh module"
    log_info "Phase 1: Infrastructure (postgres, redis)"
    log_info "Phase 2: Core Memory (memory-api)"
    log_info "Phase 3: Backend & Monitoring (backend, dev-monitoring)"
    log_info "Phase 4: Applications (experience-api, voice-storage, doc-services)"
    log_info "Phase 5: Integration (forge-bridge)"
    log_info "Phase 6: Frontend (frontend-interface)"
}

stop_services_by_phases() {
    log_info "🔧 Service shutdown will be implemented in service-manager.sh module"
    log_info "Shutdown order: Frontend → Integration → Apps → Backend → Memory → Infrastructure"
}

verify_startup_success() {
    log_info "🔧 Startup verification will be implemented in health-monitor.sh module"
}

show_services_status() {
    log_info "🔧 Service status display will be implemented in service-manager.sh module"
}

show_port_status() {
    log_info "🔧 Port status display will be implemented in port-manager.sh module"
}

show_resource_usage() {
    log_info "📊 System Resources:"
    echo "  Memory: $(free -h 2>/dev/null | grep Mem || echo 'N/A')"
    echo "  Disk: $(df -h . | tail -1)"
    echo "  Load: $(uptime | grep -o 'load average.*')"
}

run_comprehensive_health_checks() {
    log_info "🔧 Health checks will be implemented in health-monitor.sh module"
}

show_health_summary() {
    log_info "🔧 Health summary will be implemented in health-monitor.sh module"
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
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║  📝 Logs: $LOGS_DIR${NC}"
    echo -e "${GREEN}║  🔧 Config: $CONFIG_DIR${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

show_shutdown_summary() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                   🛑 GALAXY SYSTEM STOPPED                   ║${NC}"
    echo -e "${BLUE}║                                                              ║${NC}"
    echo -e "${BLUE}║  All services have been gracefully shutdown.                ║${NC}"
    echo -e "${BLUE}║  Use './galaxy-master.sh start' to restart the system.      ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

cleanup_process_files() {
    log_info "Cleaning up PID files and temporary data..."
    find "$LOGS_DIR" -name "*.pid" -delete 2>/dev/null || true
    log_debug "Process cleanup completed"
}

# ==================================================
# MAIN COMMAND DISPATCHER
# ==================================================

show_usage() {
    echo ""
    echo -e "${CYAN}🎯 GALAXY ORCHESTRATOR - Single Command System Control${NC}"
    echo ""
    echo -e "${GREEN}USAGE:${NC}"
    echo "  $0 start     - Start all Galaxy services in correct order"
    echo "  $0 stop      - Stop all Galaxy services gracefully"
    echo "  $0 restart   - Restart the entire Galaxy system"
    echo "  $0 status    - Show current system status"
    echo "  $0 health    - Run comprehensive health checks"
    echo ""
    echo -e "${GREEN}EXAMPLES:${NC}"
    echo "  $0 start                    # Start entire system"
    echo "  $0 status                   # Check what's running"
    echo "  DEBUG=true $0 start         # Start with debug output"
    echo ""
    echo -e "${GREEN}FILES:${NC}"
    echo "  Config:  $CONFIG_DIR/"
    echo "  Logs:    $LOGS_DIR/"
    echo "  Modules: $MODULES_DIR/"
    echo ""
}

main() {
    # Create initial log entry
    log_info "Galaxy Orchestrator started with command: $*"
    
    # Load orchestration modules
    source_modules
    
    # Parse command
    case "${1:-}" in
        start)
            start_all_services
            ;;
        stop)
            stop_all_services
            ;;
        restart)
            restart_all_services
            ;;
        status)
            show_system_status
            ;;
        health)
            run_health_checks
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

# ==================================================
# EXECUTION
# ==================================================

# Ensure we're in the right directory
cd "$GALAXY_ROOT"

# Run main function with all arguments
main "$@"