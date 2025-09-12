#!/bin/bash

# Policy Pilot Health Check Script
# This script checks the health of all Policy Pilot services

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="http://localhost:8000"
OPENSEARCH_URL="http://localhost:9200"
DASHBOARDS_URL="http://localhost:5601"

# Functions
log() {
    local level=$1
    shift
    local message="$*"
    
    case $level in
        "INFO")
            echo -e "${BLUE}[INFO]${NC} $message"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
    esac
}

check_api_health() {
    log "INFO" "Checking API health..."
    
    local endpoints=(
        "/api/health"
        "/api/health/live"
        "/api/health/ready"
        "/api/health/opensearch"
    )
    
    local failed_checks=()
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "$API_URL$endpoint" >/dev/null 2>&1; then
            log "SUCCESS" "API endpoint $endpoint is healthy"
        else
            log "ERROR" "API endpoint $endpoint is not responding"
            failed_checks+=("$endpoint")
        fi
    done
    
    if [ ${#failed_checks[@]} -ne 0 ]; then
        log "ERROR" "API health check failed for: ${failed_checks[*]}"
        return 1
    fi
    
    log "SUCCESS" "API health check passed"
    return 0
}

check_opensearch_health() {
    log "INFO" "Checking OpenSearch health..."
    
    if curl -f -s "$OPENSEARCH_URL/_cluster/health" >/dev/null 2>&1; then
        log "SUCCESS" "OpenSearch is healthy"
        
        # Get cluster health details
        local health_status=$(curl -s "$OPENSEARCH_URL/_cluster/health" | jq -r '.status' 2>/dev/null || echo "unknown")
        log "INFO" "OpenSearch cluster status: $health_status"
        
        if [ "$health_status" = "red" ]; then
            log "WARNING" "OpenSearch cluster is in RED status"
            return 1
        fi
    else
        log "ERROR" "OpenSearch is not responding"
        return 1
    fi
    
    return 0
}

check_dashboards_health() {
    log "INFO" "Checking OpenSearch Dashboards health..."
    
    if curl -f -s "$DASHBOARDS_URL" >/dev/null 2>&1; then
        log "SUCCESS" "OpenSearch Dashboards is healthy"
    else
        log "WARNING" "OpenSearch Dashboards is not responding"
        return 1
    fi
    
    return 0
}

check_docker_services() {
    log "INFO" "Checking Docker services..."
    
    local services=(
        "policy-pilot-api"
        "policy-pilot-opensearch"
        "policy-pilot-dashboards"
    )
    
    local failed_services=()
    
    for service in "${services[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$service"; then
            local status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$service" | awk '{print $2}')
            log "SUCCESS" "Docker service $service is running ($status)"
        else
            log "ERROR" "Docker service $service is not running"
            failed_services+=("$service")
        fi
    done
    
    if [ ${#failed_services[@]} -ne 0 ]; then
        log "ERROR" "Docker services not running: ${failed_services[*]}"
        return 1
    fi
    
    return 0
}

check_disk_space() {
    log "INFO" "Checking disk space..."
    
    local usage=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -lt 80 ]; then
        log "SUCCESS" "Disk usage is $usage% (healthy)"
    elif [ "$usage" -lt 90 ]; then
        log "WARNING" "Disk usage is $usage% (getting high)"
    else
        log "ERROR" "Disk usage is $usage% (critical)"
        return 1
    fi
    
    return 0
}

check_memory_usage() {
    log "INFO" "Checking memory usage..."
    
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$memory_usage" -lt 80 ]; then
        log "SUCCESS" "Memory usage is $memory_usage% (healthy)"
    elif [ "$memory_usage" -lt 90 ]; then
        log "WARNING" "Memory usage is $memory_usage% (getting high)"
    else
        log "ERROR" "Memory usage is $memory_usage% (critical)"
        return 1
    fi
    
    return 0
}

check_logs() {
    log "INFO" "Checking recent logs for errors..."
    
    local log_files=(
        "logs/policy_pilot.log"
        "logs/nginx/error.log"
    )
    
    local error_count=0
    
    for log_file in "${log_files[@]}"; do
        if [ -f "$log_file" ]; then
            local errors=$(grep -i "error\|exception\|failed" "$log_file" | tail -5 | wc -l)
            if [ "$errors" -gt 0 ]; then
                log "WARNING" "Found $errors recent errors in $log_file"
                error_count=$((error_count + errors))
            else
                log "SUCCESS" "No recent errors in $log_file"
            fi
        else
            log "INFO" "Log file $log_file not found"
        fi
    done
    
    if [ "$error_count" -gt 0 ]; then
        log "WARNING" "Total recent errors found: $error_count"
    fi
    
    return 0
}

show_service_urls() {
    log "INFO" "Service URLs:"
    log "INFO" "  - API: $API_URL"
    log "INFO" "  - API Docs: $API_URL/docs"
    log "INFO" "  - OpenSearch: $OPENSEARCH_URL"
    log "INFO" "  - OpenSearch Dashboards: $DASHBOARDS_URL"
}

show_quick_commands() {
    log "INFO" "Quick commands:"
    log "INFO" "  - View logs: make logs"
    log "INFO" "  - Check status: make status"
    log "INFO" "  - Restart services: make restart"
    log "INFO" "  - Stop services: make stop"
}

# Main health check process
main() {
    log "INFO" "Starting Policy Pilot health check..."
    
    local overall_status=0
    
    # Check all services
    check_api_health || overall_status=1
    check_opensearch_health || overall_status=1
    check_dashboards_health || overall_status=1
    check_docker_services || overall_status=1
    check_disk_space || overall_status=1
    check_memory_usage || overall_status=1
    check_logs
    
    echo ""
    show_service_urls
    echo ""
    show_quick_commands
    echo ""
    
    if [ $overall_status -eq 0 ]; then
        log "SUCCESS" "All health checks passed! System is healthy."
    else
        log "ERROR" "Some health checks failed. Please check the issues above."
    fi
    
    exit $overall_status
}

# Run main function
main "$@"
