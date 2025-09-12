#!/bin/bash

# Policy Pilot Restore Script
# This script restores Policy Pilot from a backup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"

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

show_help() {
    cat << EOF
Policy Pilot Restore Script

Usage: $0 [BACKUP_NAME]

Arguments:
    BACKUP_NAME    Name of the backup to restore (e.g., policy_pilot_backup_20240115_143000)

Examples:
    $0 policy_pilot_backup_20240115_143000
    $0 latest

Available backups:
$(ls -la "$BACKUP_DIR" | grep "policy_pilot_backup_" | tail -5 | awk '{print "    " $9}')

EOF
}

list_available_backups() {
    log "INFO" "Available backups:"
    ls -la "$BACKUP_DIR" | grep "policy_pilot_backup_" | while read -r line; do
        local backup_name=$(echo "$line" | awk '{print $9}')
        local backup_date=$(echo "$line" | awk '{print $6, $7, $8}')
        local backup_size=$(echo "$line" | awk '{print $5}')
        log "INFO" "  - $backup_name ($backup_date, $backup_size bytes)"
    done
}

find_backup() {
    local backup_name="$1"
    
    if [ "$backup_name" = "latest" ]; then
        # Find the most recent backup
        local latest_backup=$(ls -t "$BACKUP_DIR" | grep "policy_pilot_backup_" | head -1)
        if [ -z "$latest_backup" ]; then
            log "ERROR" "No backups found"
            return 1
        fi
        echo "$BACKUP_DIR/$latest_backup"
    else
        # Find specific backup
        local backup_path="$BACKUP_DIR/$backup_name"
        if [ ! -d "$backup_path" ]; then
            log "ERROR" "Backup not found: $backup_path"
            return 1
        fi
        echo "$backup_path"
    fi
}

verify_backup() {
    local backup_path="$1"
    
    log "INFO" "Verifying backup integrity..."
    
    # Check if backup directory exists
    if [ ! -d "$backup_path" ]; then
        log "ERROR" "Backup directory not found: $backup_path"
        return 1
    fi
    
    # Check if manifest exists
    if [ ! -f "$backup_path/backup_manifest.txt" ]; then
        log "WARNING" "Backup manifest not found. Backup may be incomplete."
    else
        log "SUCCESS" "Backup manifest found"
    fi
    
    # Check for essential files
    local essential_files=(
        "uploads.tar.gz"
        "data.tar.gz"
        "logs.tar.gz"
        "config"
    )
    
    local missing_files=()
    for file in "${essential_files[@]}"; do
        if [ ! -e "$backup_path/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -ne 0 ]; then
        log "WARNING" "Missing files in backup: ${missing_files[*]}"
    else
        log "SUCCESS" "Backup verification passed"
    fi
    
    return 0
}

stop_services() {
    log "INFO" "Stopping services before restore..."
    
    # Stop Docker services
    if command -v docker-compose &> /dev/null; then
        docker-compose down 2>/dev/null || true
        docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    fi
    
    log "SUCCESS" "Services stopped"
}

restore_application_data() {
    local backup_path="$1"
    
    log "INFO" "Restoring application data..."
    
    # Restore uploads directory
    if [ -f "$backup_path/uploads.tar.gz" ]; then
        log "INFO" "Restoring uploads directory..."
        tar -xzf "$backup_path/uploads.tar.gz" -C "$PROJECT_DIR"
        log "SUCCESS" "Uploads directory restored"
    fi
    
    # Restore data directory
    if [ -f "$backup_path/data.tar.gz" ]; then
        log "INFO" "Restoring data directory..."
        tar -xzf "$backup_path/data.tar.gz" -C "$PROJECT_DIR"
        log "SUCCESS" "Data directory restored"
    fi
    
    # Restore logs directory
    if [ -f "$backup_path/logs.tar.gz" ]; then
        log "INFO" "Restoring logs directory..."
        tar -xzf "$backup_path/logs.tar.gz" -C "$PROJECT_DIR"
        log "SUCCESS" "Logs directory restored"
    fi
    
    # Restore models directory
    if [ -f "$backup_path/models.tar.gz" ]; then
        log "INFO" "Restoring models directory..."
        tar -xzf "$backup_path/models.tar.gz" -C "$PROJECT_DIR"
        log "SUCCESS" "Models directory restored"
    fi
}

restore_configuration() {
    local backup_path="$1"
    
    log "INFO" "Restoring configuration files..."
    
    local config_dir="$backup_path/config"
    
    if [ ! -d "$config_dir" ]; then
        log "WARNING" "Configuration directory not found in backup"
        return 0
    fi
    
    # Restore environment file
    if [ -f "$config_dir/.env" ]; then
        log "INFO" "Restoring environment file..."
        cp "$config_dir/.env" "$PROJECT_DIR/"
        log "SUCCESS" "Environment file restored"
    fi
    
    # Restore Docker Compose files
    if [ -f "$config_dir/docker-compose.yml" ]; then
        cp "$config_dir/docker-compose.yml" "$PROJECT_DIR/"
    fi
    
    if [ -f "$config_dir/docker-compose.prod.yml" ]; then
        cp "$config_dir/docker-compose.prod.yml" "$PROJECT_DIR/"
    fi
    
    # Restore nginx configuration
    if [ -d "$config_dir/nginx" ]; then
        log "INFO" "Restoring nginx configuration..."
        cp -r "$config_dir/nginx" "$PROJECT_DIR/"
        log "SUCCESS" "Nginx configuration restored"
    fi
    
    # Restore scripts
    if [ -d "$config_dir/scripts" ]; then
        log "INFO" "Restoring scripts..."
        cp -r "$config_dir/scripts" "$PROJECT_DIR/"
        log "SUCCESS" "Scripts restored"
    fi
    
    log "SUCCESS" "Configuration files restored"
}

restore_opensearch_data() {
    local backup_path="$1"
    
    log "INFO" "Restoring OpenSearch data..."
    
    # Check if OpenSearch snapshots exist
    if [ ! -d "$backup_path/opensearch_snapshots" ]; then
        log "WARNING" "OpenSearch snapshots not found in backup"
        return 0
    fi
    
    # Start OpenSearch first
    log "INFO" "Starting OpenSearch..."
    docker-compose up -d opensearch
    
    # Wait for OpenSearch to be ready
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:9200/_cluster/health >/dev/null 2>&1; then
            log "SUCCESS" "OpenSearch is ready"
            break
        fi
        
        log "INFO" "Waiting for OpenSearch... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log "ERROR" "OpenSearch failed to start within expected time"
        return 1
    fi
    
    # Copy snapshots back to OpenSearch container
    log "INFO" "Copying snapshots to OpenSearch container..."
    docker cp "$backup_path/opensearch_snapshots" policy-pilot-opensearch-prod:/usr/share/opensearch/backups
    
    # Create snapshot repository
    curl -X PUT "localhost:9200/_snapshot/backup_repo" -H 'Content-Type: application/json' -d '{
        "type": "fs",
        "settings": {
            "location": "/usr/share/opensearch/backups"
        }
    }' 2>/dev/null || true
    
    # List available snapshots
    local snapshots=$(curl -s "localhost:9200/_snapshot/backup_repo/_all" | jq -r '.snapshots[].snapshot' 2>/dev/null || echo "")
    
    if [ -n "$snapshots" ]; then
        # Restore the most recent snapshot
        local latest_snapshot=$(echo "$snapshots" | tail -1)
        log "INFO" "Restoring snapshot: $latest_snapshot"
        
        if curl -X POST "localhost:9200/_snapshot/backup_repo/$latest_snapshot/_restore" >/dev/null 2>&1; then
            log "SUCCESS" "OpenSearch data restored from snapshot: $latest_snapshot"
        else
            log "WARNING" "Failed to restore OpenSearch snapshot"
        fi
    else
        log "WARNING" "No snapshots found in backup"
    fi
}

start_services() {
    log "INFO" "Starting services after restore..."
    
    # Start all services
    docker-compose up -d
    
    # Wait for services to be ready
    log "INFO" "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    if curl -f http://localhost:8000/api/health/live >/dev/null 2>&1; then
        log "SUCCESS" "Services started successfully"
    else
        log "WARNING" "Services may not be fully ready yet"
    fi
}

show_restore_info() {
    local backup_path="$1"
    
    log "SUCCESS" "Restore completed successfully!"
    log "INFO" "Restored from: $backup_path"
    log "INFO" ""
    log "INFO" "Next steps:"
    log "INFO" "1. Check service status: make status"
    log "INFO" "2. Check health: make health"
    log "INFO" "3. View logs: make logs"
    log "INFO" "4. Test API: curl http://localhost:8000/api/health"
}

# Main restore process
main() {
    local backup_name="$1"
    
    if [ -z "$backup_name" ]; then
        show_help
        exit 1
    fi
    
    log "INFO" "Starting Policy Pilot restore..."
    
    # Find backup
    local backup_path=$(find_backup "$backup_name")
    if [ $? -ne 0 ]; then
        list_available_backups
        exit 1
    fi
    
    log "INFO" "Found backup: $backup_path"
    
    # Verify backup
    verify_backup "$backup_path"
    
    # Stop services
    stop_services
    
    # Restore data
    restore_application_data "$backup_path"
    restore_configuration "$backup_path"
    restore_opensearch_data "$backup_path"
    
    # Start services
    start_services
    
    # Show restore information
    show_restore_info "$backup_path"
    
    log "SUCCESS" "Restore process completed!"
}

# Run main function
main "$@"
