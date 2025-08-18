#!/bin/bash
# ==================================================
# 🔗 DEPENDENCY RESOLVER MODULE
# ==================================================
# Galaxy Orchestrator - Dependency Resolution Functions
# Version: 1.0.0
# Created: 2025-08-18
# 
# This module handles:
# - Service dependency analysis
# - Startup order calculation
# - Circular dependency detection
# - Dependency validation
# ==================================================

# Ensure this script is sourced, not executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "❌ This script should be sourced, not executed directly"
    exit 1
fi

# ==================================================
# DEPENDENCY RESOLVER CONFIGURATION
# ==================================================

# Service dependency mappings
declare -A SERVICE_DEPENDENCIES
SERVICE_DEPENDENCIES["postgres"]=""
SERVICE_DEPENDENCIES["redis"]=""
SERVICE_DEPENDENCIES["memory-api"]="postgres"
SERVICE_DEPENDENCIES["backend"]="memory-api postgres redis"
SERVICE_DEPENDENCIES["dev-monitoring"]=""
SERVICE_DEPENDENCIES["experience-api"]=""
SERVICE_DEPENDENCIES["voice-storage"]=""
SERVICE_DEPENDENCIES["doc-system-api"]=""
SERVICE_DEPENDENCIES["doc-system-simple"]=""
SERVICE_DEPENDENCIES["standards-web-dashboard"]=""
SERVICE_DEPENDENCIES["forge-bridge"]="backend"
SERVICE_DEPENDENCIES["frontend-interface"]="backend dev-monitoring"

# Service level mappings (for topological sort)
declare -A SERVICE_LEVELS
SERVICE_LEVELS["postgres"]="0"
SERVICE_LEVELS["redis"]="0"
SERVICE_LEVELS["memory-api"]="1"
SERVICE_LEVELS["backend"]="2"
SERVICE_LEVELS["dev-monitoring"]="2"
SERVICE_LEVELS["experience-api"]="3"
SERVICE_LEVELS["voice-storage"]="3"
SERVICE_LEVELS["doc-system-api"]="3"
SERVICE_LEVELS["doc-system-simple"]="3"
SERVICE_LEVELS["standards-web-dashboard"]="3"
SERVICE_LEVELS["forge-bridge"]="4"
SERVICE_LEVELS["frontend-interface"]="5"

# Wait times between dependency levels
declare -A LEVEL_WAIT_TIMES
LEVEL_WAIT_TIMES["0"]="10"  # Infrastructure services
LEVEL_WAIT_TIMES["1"]="15"  # Core memory
LEVEL_WAIT_TIMES["2"]="20"  # Backend and monitoring
LEVEL_WAIT_TIMES["3"]="10"  # Application services
LEVEL_WAIT_TIMES["4"]="10"  # Integration services
LEVEL_WAIT_TIMES["5"]="5"   # Frontend

# ==================================================
# DEPENDENCY VALIDATION FUNCTIONS
# ==================================================

validate_service_dependencies() {
    log_info "🔍 Validating service dependencies..."
    
    local validation_errors=0
    
    # Check for circular dependencies
    if ! check_circular_dependencies; then
        log_error "Circular dependencies detected!"
        ((validation_errors++))
    fi
    
    # Validate each service's dependencies exist
    for service in "${!SERVICE_DEPENDENCIES[@]}"; do
        local deps="${SERVICE_DEPENDENCIES[$service]}"
        
        if [[ -n "$deps" ]]; then
            for dep in $deps; do
                if [[ ! -v "SERVICE_DEPENDENCIES[$dep]" ]]; then
                    log_error "Service $service depends on unknown service: $dep"
                    ((validation_errors++))
                fi
            done
        fi
    done
    
    # Validate service levels are consistent
    if ! validate_dependency_levels; then
        log_error "Dependency levels are inconsistent!"
        ((validation_errors++))
    fi
    
    if [[ $validation_errors -eq 0 ]]; then
        log_success "✅ Dependency validation passed"
        return 0
    else
        log_error "❌ Dependency validation failed with $validation_errors errors"
        return 1
    fi
}

check_circular_dependencies() {
    log_debug "Checking for circular dependencies..."
    
    # Use DFS to detect cycles
    declare -A visited
    declare -A recursion_stack
    
    for service in "${!SERVICE_DEPENDENCIES[@]}"; do
        if [[ "${visited[$service]:-false}" == "false" ]]; then
            if detect_cycle_dfs "$service" visited recursion_stack; then
                return 1  # Cycle detected
            fi
        fi
    done
    
    log_debug "No circular dependencies found"
    return 0  # No cycles
}

detect_cycle_dfs() {
    local service="$1"
    local -n visited_ref=$2
    local -n stack_ref=$3
    
    visited_ref["$service"]="true"
    stack_ref["$service"]="true"
    
    local deps="${SERVICE_DEPENDENCIES[$service]}"
    if [[ -n "$deps" ]]; then
        for dep in $deps; do
            if [[ "${visited_ref[$dep]:-false}" == "false" ]]; then
                if detect_cycle_dfs "$dep" visited_ref stack_ref; then
                    return 1  # Cycle found in subtree
                fi
            elif [[ "${stack_ref[$dep]:-false}" == "true" ]]; then
                log_error "Circular dependency detected: $service -> $dep"
                return 1  # Back edge found (cycle)
            fi
        done
    fi
    
    stack_ref["$service"]="false"
    return 0  # No cycle in this branch
}

validate_dependency_levels() {
    log_debug "Validating dependency levels..."
    
    for service in "${!SERVICE_DEPENDENCIES[@]}"; do
        local service_level="${SERVICE_LEVELS[$service]}"
        local deps="${SERVICE_DEPENDENCIES[$service]}"
        
        if [[ -n "$deps" ]]; then
            for dep in $deps; do
                local dep_level="${SERVICE_LEVELS[$dep]}"
                
                if [[ $dep_level -ge $service_level ]]; then
                    log_error "Invalid dependency level: $service (level $service_level) depends on $dep (level $dep_level)"
                    return 1
                fi
            done
        fi
    done
    
    log_debug "Dependency levels are valid"
    return 0
}

# ==================================================
# STARTUP ORDER CALCULATION
# ==================================================

calculate_startup_order() {
    log_info "📋 Calculating optimal startup order..."
    
    # Group services by dependency level
    declare -A level_groups
    
    for service in "${!SERVICE_LEVELS[@]}"; do
        local level="${SERVICE_LEVELS[$service]}"
        if [[ -n "${level_groups[$level]}" ]]; then
            level_groups["$level"]+=" $service"
        else
            level_groups["$level"]="$service"
        fi
    done
    
    # Sort levels numerically
    local sorted_levels=($(printf '%s\n' "${!level_groups[@]}" | sort -n))
    
    log_info "Startup order by dependency levels:"
    for level in "${sorted_levels[@]}"; do
        local services="${level_groups[$level]}"
        local wait_time="${LEVEL_WAIT_TIMES[$level]:-5}"
        
        log_info "  Level $level: $services (wait ${wait_time}s after)"
    done
    
    return 0
}

get_services_by_level() {
    local target_level="$1"
    local services="${level_groups[$target_level]:-}"
    echo "$services"
}

# ==================================================
# DEPENDENCY-AWARE SERVICE CONTROL
# ==================================================

start_service_with_dependencies() {
    local service_name="$1"
    local force_restart="${2:-false}"
    
    log_info "🚀 Starting $service_name with dependency resolution..."
    
    # Check if dependencies are met
    if ! check_service_dependencies_met "$service_name"; then
        log_info "Starting dependencies for $service_name..."
        start_service_dependencies "$service_name"
    fi
    
    # Start the service itself
    start_service "$service_name"
    
    # Verify dependencies are still healthy
    if ! verify_service_dependencies "$service_name"; then
        log_warning "Some dependencies for $service_name are not healthy"
        return 1
    fi
    
    return 0
}

check_service_dependencies_met() {
    local service_name="$1"
    local deps="${SERVICE_DEPENDENCIES[$service_name]}"
    
    if [[ -z "$deps" ]]; then
        log_debug "$service_name has no dependencies"
        return 0
    fi
    
    log_debug "Checking dependencies for $service_name: $deps"
    
    for dep in $deps; do
        local dep_status=$(get_service_status "$dep")
        
        if [[ "$dep_status" != "running" ]]; then
            log_debug "Dependency $dep is not running (status: $dep_status)"
            return 1
        fi
    done
    
    log_debug "All dependencies for $service_name are running"
    return 0
}

start_service_dependencies() {
    local service_name="$1"
    local deps="${SERVICE_DEPENDENCIES[$service_name]}"
    
    if [[ -z "$deps" ]]; then
        return 0
    fi
    
    log_info "Starting dependencies for $service_name: $deps"
    
    for dep in $deps; do
        local dep_status=$(get_service_status "$dep")
        
        if [[ "$dep_status" != "running" ]]; then
            log_info "Starting dependency: $dep"
            
            # Recursively start dependencies of dependencies
            start_service_with_dependencies "$dep"
            
            # Wait for dependency to be ready
            wait_for_service_ready "$dep"
        else
            log_debug "Dependency $dep is already running"
        fi
    done
}

verify_service_dependencies() {
    local service_name="$1"
    local deps="${SERVICE_DEPENDENCIES[$service_name]}"
    
    if [[ -z "$deps" ]]; then
        return 0
    fi
    
    local unhealthy_deps=()
    
    for dep in $deps; do
        if ! is_service_healthy "$dep"; then
            unhealthy_deps+=("$dep")
        fi
    done
    
    if [[ ${#unhealthy_deps[@]} -eq 0 ]]; then
        log_debug "All dependencies for $service_name are healthy"
        return 0
    else
        log_warning "Unhealthy dependencies for $service_name: ${unhealthy_deps[*]}"
        return 1
    fi
}

# ==================================================
# SERVICE READINESS FUNCTIONS
# ==================================================

wait_for_service_ready() {
    local service_name="$1"
    local timeout="${2:-60}"  # Default 60 seconds timeout
    local check_interval="${3:-2}"  # Default 2 seconds check interval
    
    log_info "⏳ Waiting for $service_name to be ready (timeout: ${timeout}s)..."
    
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        if is_service_ready "$service_name"; then
            log_success "✅ $service_name is ready"
            return 0
        fi
        
        log_debug "$service_name not ready yet, waiting..."
        sleep "$check_interval"
        ((elapsed += check_interval))
    done
    
    log_error "❌ Timeout waiting for $service_name to be ready"
    return 1
}

is_service_ready() {
    local service_name="$1"
    local service_type="${SERVICE_TYPES[$service_name]}"
    
    # Check if service is running
    local status=$(get_service_status "$service_name")
    if [[ "$status" != "running" && "$status" != "static" ]]; then
        return 1
    fi
    
    # For services with health endpoints, check health
    case "$service_name" in
        "backend"|"memory-api"|"experience-api"|"voice-storage")
            return $(is_service_healthy "$service_name")
            ;;
        "postgres"|"redis")
            # For external services, running status is sufficient
            return 0
            ;;
        *)
            # For other services, assume ready if running
            return 0
            ;;
    esac
}

is_service_healthy() {
    local service_name="$1"
    local port="${SERVICE_PORTS[$service_name]}"
    
    # Handle services with multiple ports
    if [[ "$port" == *","* ]]; then
        port="${port%%,*}"  # Use first port
    fi
    
    # Determine health endpoint
    local health_endpoint
    case "$service_name" in
        "backend"|"memory-api"|"voice-storage")
            health_endpoint="/health"
            ;;
        "experience-api")
            health_endpoint="/api/health"
            ;;
        "standards-web-dashboard")
            health_endpoint="/metrics"
            ;;
        *)
            # For services without specific health endpoints, just check if port is open
            if nc -z localhost "$port" 2>/dev/null; then
                return 0
            else
                return 1
            fi
            ;;
    esac
    
    # Perform health check
    if curl -sf "http://localhost:${port}${health_endpoint}" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# ==================================================
# DEPENDENCY IMPACT ANALYSIS
# ==================================================

get_dependent_services() {
    local target_service="$1"
    local dependents=()
    
    for service in "${!SERVICE_DEPENDENCIES[@]}"; do
        local deps="${SERVICE_DEPENDENCIES[$service]}"
        
        if [[ -n "$deps" ]]; then
            for dep in $deps; do
                if [[ "$dep" == "$target_service" ]]; then
                    dependents+=("$service")
                    break
                fi
            done
        fi
    done
    
    echo "${dependents[*]}"
}

analyze_service_impact() {
    local service_name="$1"
    
    log_info "🔍 Analyzing impact of stopping $service_name..."
    
    local direct_dependents=($(get_dependent_services "$service_name"))
    local all_affected=()
    
    # Find all services that would be affected (recursive)
    find_all_affected_services "$service_name" all_affected
    
    if [[ ${#all_affected[@]} -eq 0 ]]; then
        log_info "✅ No other services depend on $service_name"
    else
        log_warning "⚠️  Stopping $service_name would affect: ${all_affected[*]}"
        
        # Check if any critical services would be affected
        local critical_affected=()
        for affected in "${all_affected[@]}"; do
            if [[ "${SERVICE_CRITICAL[$affected]}" == "true" ]]; then
                critical_affected+=("$affected")
            fi
        done
        
        if [[ ${#critical_affected[@]} -gt 0 ]]; then
            log_error "🚨 Critical services would be affected: ${critical_affected[*]}"
            return 1
        fi
    fi
    
    return 0
}

find_all_affected_services() {
    local target_service="$1"
    local -n affected_ref=$2
    local direct_dependents=($(get_dependent_services "$target_service"))
    
    for dependent in "${direct_dependents[@]}"; do
        # Add to affected list if not already there
        if [[ ! " ${affected_ref[*]} " =~ " $dependent " ]]; then
            affected_ref+=("$dependent")
            
            # Recursively find services that depend on this dependent
            find_all_affected_services "$dependent" affected_ref
        fi
    done
}

# ==================================================
# DEPENDENCY GRAPH UTILITIES
# ==================================================

show_dependency_graph() {
    log_info "📊 Service Dependency Graph:"
    echo ""
    
    # Show services grouped by level
    local levels=($(printf '%s\n' "${!SERVICE_LEVELS[@]}" | sort -n | uniq))
    
    for level in "${levels[@]}"; do
        echo -e "${CYAN}Level $level:${NC}"
        
        for service in "${!SERVICE_LEVELS[@]}"; do
            if [[ "${SERVICE_LEVELS[$service]}" == "$level" ]]; then
                local deps="${SERVICE_DEPENDENCIES[$service]}"
                local is_critical="${SERVICE_CRITICAL[$service]}"
                local critical_marker=""
                
                if [[ "$is_critical" == "true" ]]; then
                    critical_marker=" ${RED}[CRITICAL]${NC}"
                fi
                
                if [[ -n "$deps" ]]; then
                    echo -e "  ${GREEN}$service${NC}$critical_marker → depends on: $deps"
                else
                    echo -e "  ${GREEN}$service${NC}$critical_marker → no dependencies"
                fi
            fi
        done
        echo ""
    done
}

export_dependency_graph() {
    local output_file="$LOGS_DIR/dependency_graph.dot"
    
    log_info "📝 Exporting dependency graph to: $output_file"
    
    cat > "$output_file" << 'EOF'
digraph GalaxyServices {
    rankdir=TB;
    node [shape=box, style=filled];
    
    // Infrastructure layer
    subgraph cluster_0 {
        label="Infrastructure (Level 0)";
        color=blue;
        postgres [fillcolor=lightblue];
        redis [fillcolor=lightblue];
    }
    
    // Core services layer  
    subgraph cluster_1 {
        label="Core Services (Level 1-2)";
        color=green;
        "memory-api" [fillcolor=lightgreen];
        backend [fillcolor=lightgreen];
        "dev-monitoring" [fillcolor=lightgreen];
    }
    
    // Application layer
    subgraph cluster_2 {
        label="Applications (Level 3-4)";
        color=yellow;
        "experience-api" [fillcolor=lightyellow];
        "voice-storage" [fillcolor=lightyellow];
        "doc-system-api" [fillcolor=lightyellow];
        "standards-web-dashboard" [fillcolor=lightyellow];
        "forge-bridge" [fillcolor=lightyellow];
    }
    
    // Frontend layer
    subgraph cluster_3 {
        label="Frontend (Level 5)";
        color=orange;
        "frontend-interface" [fillcolor=orange];
    }
    
    // Dependencies
EOF

    # Add dependency edges
    for service in "${!SERVICE_DEPENDENCIES[@]}"; do
        local deps="${SERVICE_DEPENDENCIES[$service]}"
        
        if [[ -n "$deps" ]]; then
            for dep in $deps; do
                echo "    \"$dep\" -> \"$service\";" >> "$output_file"
            done
        fi
    done
    
    echo "}" >> "$output_file"
    
    log_success "Dependency graph exported to $output_file"
}

# ==================================================
# MODULE INITIALIZATION
# ==================================================

log_debug "Dependency Resolver module loaded successfully"