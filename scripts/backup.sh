#!/bin/bash

# Policy Pilot Backup Script
# This script creates backups of Policy Pilot data and configuration

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
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="policy_pilot_backup_${DATE}"

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

create_backup_directory() {
    log "INFO" "Creating backup directory..."
    
    local backup_path="${BACKUP_DIR}/${BACKUP_NAME}"
    mkdir -p "$backup_path"
    
    log "SUCCESS" "Backup directory created: $backup_path"
    echo "$backup_path"
}

backup_opensearch_data() {
    log "INFO" "Backing up OpenSearch data..."
    
    local backup_path="$1"
    
    # Check if OpenSearch is running
    if ! docker ps | grep -q "policy-pilot-opensearch"; then
        log "WARNING" "OpenSearch is not running. Skipping OpenSearch backup."
        return 0
    fi
    
    # Create OpenSearch snapshot
    local snapshot_name="backup_${DATE}"
    
    # Create snapshot repository if it doesn't exist
    curl -X PUT "localhost:9200/_snapshot/backup_repo" -H 'Content-Type: application/json' -d '{
        "type": "fs",
        "settings": {
            "location": "/usr/share/opensearch/backups"
        }
    }' 2>/dev/null || true
    
    # Create snapshot
    if curl -X PUT "localhost:9200/_snapshot/backup_repo/${snapshot_name}?wait_for_completion=true" >/dev/null 2>&1; then
        log "SUCCESS" "OpenSearch snapshot created: $snapshot_name"
        
        # Copy snapshot to backup directory
        docker cp policy-pilot-opensearch-prod:/usr/share/opensearch/backups "${backup_path}/opensearch_snapshots" 2>/dev/null || true
    else
        log "WARNING" "Failed to create OpenSearch snapshot"
    fi
}

backup_application_data() {
    log "INFO" "Backing up application data..."
    
    local backup_path="$1"
    
    # Backup uploads directory
    if [ -d "${PROJECT_DIR}/uploads" ]; then
        log "INFO" "Backing up uploads directory..."
        tar -czf "${backup_path}/uploads.tar.gz" -C "${PROJECT_DIR}" uploads/
        log "SUCCESS" "Uploads directory backed up"
    fi
    
    # Backup data directory
    if [ -d "${PROJECT_DIR}/data" ]; then
        log "INFO" "Backing up data directory..."
        tar -czf "${backup_path}/data.tar.gz" -C "${PROJECT_DIR}" data/
        log "SUCCESS" "Data directory backed up"
    fi
    
    # Backup logs directory
    if [ -d "${PROJECT_DIR}/logs" ]; then
        log "INFO" "Backing up logs directory..."
        tar -czf "${backup_path}/logs.tar.gz" -C "${PROJECT_DIR}" logs/
        log "SUCCESS" "Logs directory backed up"
    fi
    
    # Backup models directory
    if [ -d "${PROJECT_DIR}/models" ]; then
        log "INFO" "Backing up models directory..."
        tar -czf "${backup_path}/models.tar.gz" -C "${PROJECT_DIR}" models/
        log "SUCCESS" "Models directory backed up"
    fi
}

backup_configuration() {
    log "INFO" "Backing up configuration files..."
    
    local backup_path="$1"
    local config_dir="${backup_path}/config"
    mkdir -p "$config_dir"
    
    # Backup environment files
    if [ -f "${PROJECT_DIR}/.env" ]; then
        cp "${PROJECT_DIR}/.env" "$config_dir/"
        log "SUCCESS" "Environment file backed up"
    fi
    
    # Backup Docker Compose files
    if [ -f "${PROJECT_DIR}/docker-compose.yml" ]; then
        cp "${PROJECT_DIR}/docker-compose.yml" "$config_dir/"
    fi
    
    if [ -f "${PROJECT_DIR}/docker-compose.prod.yml" ]; then
        cp "${PROJECT_DIR}/docker-compose.prod.yml" "$config_dir/"
    fi
    
    # Backup nginx configuration
    if [ -d "${PROJECT_DIR}/nginx" ]; then
        cp -r "${PROJECT_DIR}/nginx" "$config_dir/"
        log "SUCCESS" "Nginx configuration backed up"
    fi
    
    # Backup scripts
    if [ -d "${PROJECT_DIR}/scripts" ]; then
        cp -r "${PROJECT_DIR}/scripts" "$config_dir/"
        log "SUCCESS" "Scripts backed up"
    fi
    
    log "SUCCESS" "Configuration files backed up"
}

create_backup_manifest() {
    log "INFO" "Creating backup manifest..."
    
    local backup_path="$1"
    local manifest_file="${backup_path}/backup_manifest.txt"
    
    cat > "$manifest_file" << EOF
Policy Pilot Backup Manifest
============================
Backup Date: $(date)
Backup Name: $BACKUP_NAME
Backup Path: $backup_path

Contents:
EOF
    
    # List all files in backup
    find "$backup_path" -type f -exec ls -la {} \; >> "$manifest_file"
    
    # Add system information
    cat >> "$manifest_file" << EOF

System Information:
==================
OS: $(uname -a)
Docker Version: $(docker --version 2>/dev/null || echo "Not available")
Disk Usage: $(df -h . | tail -1)
Memory Usage: $(free -h | head -2 | tail -1)

OpenSearch Status:
==================
EOF
    
    # Add OpenSearch status if available
    if docker ps | grep -q "policy-pilot-opensearch"; then
        curl -s "localhost:9200/_cluster/health" >> "$manifest_file" 2>/dev/null || echo "OpenSearch not responding" >> "$manifest_file"
    else
        echo "OpenSearch not running" >> "$manifest_file"
    fi
    
    log "SUCCESS" "Backup manifest created: $manifest_file"
}

cleanup_old_backups() {
    log "INFO" "Cleaning up old backups..."
    
    local retention_days=7
    local cutoff_date=$(date -d "$retention_days days ago" +%Y%m%d 2>/dev/null || date -v-${retention_days}d +%Y%m%d)
    
    # Find and remove old backups
    find "$BACKUP_DIR" -name "policy_pilot_backup_*" -type d | while read -r backup_dir; do
        local backup_date=$(basename "$backup_dir" | sed 's/policy_pilot_backup_//' | cut -d'_' -f1)
        if [ "$backup_date" -lt "$cutoff_date" ]; then
            log "INFO" "Removing old backup: $backup_dir"
            rm -rf "$backup_dir"
        fi
    done
    
    log "SUCCESS" "Old backups cleaned up (retention: $retention_days days)"
}

show_backup_info() {
    local backup_path="$1"
    
    log "SUCCESS" "Backup completed successfully!"
    log "INFO" "Backup location: $backup_path"
    log "INFO" "Backup size: $(du -sh "$backup_path" | cut -f1)"
    log "INFO" ""
    log "INFO" "To restore this backup, run:"
    log "INFO" "  ./scripts/restore.sh $BACKUP_NAME"
    log "INFO" ""
    log "INFO" "Available backups:"
    ls -la "$BACKUP_DIR" | grep "policy_pilot_backup_" | tail -5
}

# Main backup process
main() {
    log "INFO" "Starting Policy Pilot backup..."
    
    # Create backup directory
    local backup_path=$(create_backup_directory)
    
    # Perform backups
    backup_opensearch_data "$backup_path"
    backup_application_data "$backup_path"
    backup_configuration "$backup_path"
    create_backup_manifest "$backup_path"
    cleanup_old_backups
    
    # Show backup information
    show_backup_info "$backup_path"
    
    log "SUCCESS" "Backup process completed!"
}

# Run main function
main "$@"
