#!/bin/bash

# Policy Pilot Setup Script
# This script helps set up the Policy Pilot development environment

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

check_prerequisites() {
    log "INFO" "Checking prerequisites..."
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        log "ERROR" "Python 3 is not installed. Please install Python 3.9+ first."
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$python_version < 3.9" | bc -l) -eq 1 ]]; then
        log "ERROR" "Python 3.9+ is required. Current version: $python_version"
        exit 1
    fi
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        log "WARNING" "Node.js is not installed. Frontend features may not work."
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log "WARNING" "Docker is not installed. You'll need Docker for OpenSearch."
    fi
    
    log "SUCCESS" "Prerequisites check completed"
}

create_directories() {
    log "INFO" "Creating necessary directories..."
    
    local dirs=(
        "uploads"
        "data"
        "logs"
        "models"
        "backups"
        "nginx/ssl"
        "tests/data/sample_documents"
        "tests/data/expected_outputs"
        "tests/fixtures"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$PROJECT_DIR/$dir" ]; then
            mkdir -p "$PROJECT_DIR/$dir"
            log "INFO" "Created directory: $dir"
        fi
    done
    
    log "SUCCESS" "Directories created"
}

setup_environment() {
    log "INFO" "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log "INFO" "Creating .env file..."
        cat > "$PROJECT_DIR/.env" << EOF
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# OpenSearch Configuration
OPENSEARCH_URL=http://localhost:9200

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"]

# Logging
LOG_LEVEL=INFO
EOF
        log "SUCCESS" "Created .env file"
    else
        log "INFO" ".env file already exists"
    fi
}

install_dependencies() {
    log "INFO" "Installing Python dependencies..."
    
    cd "$PROJECT_DIR"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log "INFO" "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install Python dependencies
    log "INFO" "Installing Python packages..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Install development dependencies
    log "INFO" "Installing development dependencies..."
    pip install pytest pytest-cov black isort flake8 mypy
    
    log "SUCCESS" "Python dependencies installed"
    
    # Install Node.js dependencies if Node.js is available
    if command -v npm &> /dev/null; then
        log "INFO" "Installing Node.js dependencies..."
        npm install
        log "SUCCESS" "Node.js dependencies installed"
    else
        log "WARNING" "Skipping Node.js dependencies (npm not found)"
    fi
}

setup_database() {
    log "INFO" "Setting up database..."
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        log "WARNING" "Docker not available. Please install Docker and run:"
        log "WARNING" "  docker-compose up -d opensearch opensearch-dashboards"
        return 0
    fi
    
    # Start OpenSearch
    log "INFO" "Starting OpenSearch..."
    docker-compose up -d opensearch opensearch-dashboards
    
    # Wait for OpenSearch to be ready
    log "INFO" "Waiting for OpenSearch to be ready..."
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
}

run_tests() {
    log "INFO" "Running tests..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Run basic tests
    if pytest tests/ -v --tb=short; then
        log "SUCCESS" "Tests passed"
    else
        log "WARNING" "Some tests failed. This is normal for initial setup."
    fi
}

show_next_steps() {
    log "SUCCESS" "Setup completed successfully!"
    log "INFO" "Next steps:"
    log "INFO" "1. Update your OpenAI API key in .env file"
    log "INFO" "2. Start the development server:"
    log "INFO" "   make dev"
    log "INFO" "   or"
    log "INFO" "   python src/main.py"
    log "INFO" "3. Visit http://localhost:8000/docs for API documentation"
    log "INFO" "4. Visit http://localhost:5601 for OpenSearch dashboards"
    log "INFO" ""
    log "INFO" "Useful commands:"
    log "INFO" "  make help          - Show all available commands"
    log "INFO" "  make test          - Run tests"
    log "INFO" "  make logs          - View logs"
    log "INFO" "  make health        - Check health endpoints"
    log "INFO" "  make clean         - Clean up temporary files"
}

# Main setup process
main() {
    log "INFO" "Starting Policy Pilot setup..."
    
    check_prerequisites
    create_directories
    setup_environment
    install_dependencies
    setup_database
    run_tests
    show_next_steps
    
    log "SUCCESS" "Setup completed!"
}

# Run main function
main "$@"
