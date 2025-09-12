#!/bin/bash

# Policy Pilot Deployment Script
# This script automates the deployment of Policy Pilot in production

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
ENV_FILE="${PROJECT_DIR}/.env.prod"
DOCKER_COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
BACKUP_DIR="${PROJECT_DIR}/backups"
LOG_FILE="${PROJECT_DIR}/logs/deploy.log"

# Default values
ENVIRONMENT="production"
SERVICES="all"
SKIP_TESTS=false
SKIP_BACKUP=false
FORCE_DEPLOY=false
VERBOSE=false

# Functions
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
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
    
    # Log to file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

show_help() {
    cat << EOF
Policy Pilot Deployment Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment ENV    Environment to deploy (default: production)
    -s, --services SERVICES  Services to deploy (default: all)
    -t, --skip-tests        Skip running tests before deployment
    -b, --skip-backup       Skip creating backup before deployment
    -f, --force             Force deployment even if tests fail
    -v, --verbose           Enable verbose output
    -h, --help              Show this help message

Examples:
    $0                                    # Deploy all services in production
    $0 -e staging -s api                  # Deploy only API service in staging
    $0 -t -b                              # Deploy without tests and backup
    $0 -f                                 # Force deployment

Services:
    all          Deploy all services
    api          Deploy only API service
    opensearch   Deploy only OpenSearch
    nginx        Deploy only Nginx
    redis        Deploy only Redis

EOF
}

check_prerequisites() {
    log "INFO" "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log "ERROR" "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log "ERROR" "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        log "ERROR" "Environment file not found: $ENV_FILE"
        log "INFO" "Please create the environment file with required variables."
        exit 1
    fi
    
    # Check if Docker Compose file exists
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        log "ERROR" "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    log "SUCCESS" "Prerequisites check passed"
}

validate_environment() {
    log "INFO" "Validating environment variables..."
    
    # Source environment file
    set -a
    source "$ENV_FILE"
    set +a
    
    # Required variables
    local required_vars=(
        "OPENAI_API_KEY"
        "OPENSEARCH_PASSWORD"
        "SECRET_KEY"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log "ERROR" "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            log "ERROR" "  - $var"
        done
        exit 1
    fi
    
    log "SUCCESS" "Environment validation passed"
}

create_directories() {
    log "INFO" "Creating necessary directories..."
    
    local dirs=(
        "$BACKUP_DIR"
        "${PROJECT_DIR}/logs"
        "${PROJECT_DIR}/uploads"
        "${PROJECT_DIR}/data"
        "${PROJECT_DIR}/models"
        "${PROJECT_DIR}/nginx/ssl"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log "INFO" "Created directory: $dir"
        fi
    done
    
    log "SUCCESS" "Directories created"
}

run_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        log "WARNING" "Skipping tests"
        return 0
    fi
    
    log "INFO" "Running tests..."
    
    # Check if tests directory exists
    if [ ! -d "${PROJECT_DIR}/tests" ]; then
        log "WARNING" "Tests directory not found, skipping tests"
        return 0
    fi
    
    # Run tests
    cd "$PROJECT_DIR"
    if python -m pytest tests/ -v; then
        log "SUCCESS" "Tests passed"
    else
        if [ "$FORCE_DEPLOY" = true ]; then
            log "WARNING" "Tests failed but force deployment is enabled"
        else
            log "ERROR" "Tests failed. Use -f to force deployment."
            exit 1
        fi
    fi
}

create_backup() {
    if [ "$SKIP_BACKUP" = true ]; then
        log "WARNING" "Skipping backup"
        return 0
    fi
    
    log "INFO" "Creating backup..."
    
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="${BACKUP_DIR}/backup_${backup_timestamp}"
    
    mkdir -p "$backup_path"
    
    # Backup OpenSearch data
    if docker ps | grep -q "policy-pilot-opensearch"; then
        log "INFO" "Backing up OpenSearch data..."
        docker exec policy-pilot-opensearch-prod \
            curl -X POST "localhost:9200/_snapshot/backup_repo/snapshot_${backup_timestamp}?wait_for_completion=true" || true
    fi
    
    # Backup application data
    if [ -d "${PROJECT_DIR}/uploads" ]; then
        log "INFO" "Backing up uploads..."
        tar -czf "${backup_path}/uploads.tar.gz" -C "${PROJECT_DIR}" uploads/
    fi
    
    if [ -d "${PROJECT_DIR}/data" ]; then
        log "INFO" "Backing up data..."
        tar -czf "${backup_path}/data.tar.gz" -C "${PROJECT_DIR}" data/
    fi
    
    if [ -d "${PROJECT_DIR}/logs" ]; then
        log "INFO" "Backing up logs..."
        tar -czf "${backup_path}/logs.tar.gz" -C "${PROJECT_DIR}" logs/
    fi
    
    # Cleanup old backups (keep 7 days)
    find "$BACKUP_DIR" -name "backup_*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    log "SUCCESS" "Backup created: $backup_path"
}

build_images() {
    log "INFO" "Building Docker images..."
    
    cd "$PROJECT_DIR"
    
    if [ "$SERVICES" = "all" ] || [ "$SERVICES" = "api" ]; then
        log "INFO" "Building API image..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" build policy-pilot-api
    fi
    
    if [ "$SERVICES" = "all" ] || [ "$SERVICES" = "nginx" ]; then
        log "INFO" "Building Nginx image..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" build nginx
    fi
    
    log "SUCCESS" "Docker images built"
}

deploy_services() {
    log "INFO" "Deploying services..."
    
    cd "$PROJECT_DIR"
    
    # Stop existing services
    log "INFO" "Stopping existing services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    
    # Start services
    log "INFO" "Starting services..."
    if [ "$SERVICES" = "all" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    else
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d "$SERVICES"
    fi
    
    log "SUCCESS" "Services deployed"
}

wait_for_services() {
    log "INFO" "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "INFO" "Health check attempt $attempt/$max_attempts"
        
        if curl -f http://localhost:8000/api/health/live >/dev/null 2>&1; then
            log "SUCCESS" "Services are ready"
            return 0
        fi
        
        sleep 10
        ((attempt++))
    done
    
    log "ERROR" "Services failed to become ready within expected time"
    return 1
}

run_health_checks() {
    log "INFO" "Running health checks..."
    
    local health_endpoints=(
        "http://localhost:8000/api/health"
        "http://localhost:8000/api/health/live"
        "http://localhost:8000/api/health/ready"
        "http://localhost:8000/api/health/opensearch"
    )
    
    local failed_checks=()
    
    for endpoint in "${health_endpoints[@]}"; do
        if curl -f "$endpoint" >/dev/null 2>&1; then
            log "SUCCESS" "Health check passed: $endpoint"
        else
            log "ERROR" "Health check failed: $endpoint"
            failed_checks+=("$endpoint")
        fi
    done
    
    if [ ${#failed_checks[@]} -ne 0 ]; then
        log "ERROR" "Some health checks failed:"
        for endpoint in "${failed_checks[@]}"; do
            log "ERROR" "  - $endpoint"
        done
        return 1
    fi
    
    log "SUCCESS" "All health checks passed"
}

show_deployment_info() {
    log "INFO" "Deployment completed successfully!"
    log "INFO" "Service URLs:"
    log "INFO" "  - API: http://localhost:8000"
    log "INFO" "  - API Docs: http://localhost:8000/docs"
    log "INFO" "  - OpenSearch: http://localhost:9200"
    log "INFO" "  - OpenSearch Dashboards: http://localhost:5601"
    log "INFO" "  - Redis: localhost:6379"
    
    log "INFO" "Useful commands:"
    log "INFO" "  - View logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
    log "INFO" "  - Stop services: docker-compose -f $DOCKER_COMPOSE_FILE down"
    log "INFO" "  - Restart services: docker-compose -f $DOCKER_COMPOSE_FILE restart"
    log "INFO" "  - Check status: docker-compose -f $DOCKER_COMPOSE_FILE ps"
}

cleanup() {
    log "INFO" "Cleaning up..."
    # Add any cleanup tasks here
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--services)
            SERVICES="$2"
            shift 2
            ;;
        -t|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -b|--skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        -f|--force)
            FORCE_DEPLOY=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main deployment process
main() {
    log "INFO" "Starting Policy Pilot deployment..."
    log "INFO" "Environment: $ENVIRONMENT"
    log "INFO" "Services: $SERVICES"
    
    # Set up error handling
    trap cleanup EXIT
    
    # Run deployment steps
    check_prerequisites
    validate_environment
    create_directories
    run_tests
    create_backup
    build_images
    deploy_services
    wait_for_services
    run_health_checks
    show_deployment_info
    
    log "SUCCESS" "Deployment completed successfully!"
}

# Run main function
main "$@"
