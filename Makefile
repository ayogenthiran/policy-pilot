# Policy Pilot Makefile
# Provides convenient commands for development and deployment

.PHONY: help install dev prod test clean backup restore logs status health

# Default target
help:
	@echo "Policy Pilot - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     Install dependencies"
	@echo "  dev         Start development environment"
	@echo "  test        Run tests"
	@echo "  clean       Clean up temporary files"
	@echo ""
	@echo "Production:"
	@echo "  prod        Start production environment"
	@echo "  deploy      Deploy to production"
	@echo "  backup      Create backup"
	@echo "  restore     Restore from backup"
	@echo ""
	@echo "Monitoring:"
	@echo "  logs        View logs"
	@echo "  status      Check service status"
	@echo "  health      Check health endpoints"
	@echo ""
	@echo "Utilities:"
	@echo "  setup       Initial setup"
	@echo "  update      Update dependencies"
	@echo "  lint        Run linting"
	@echo "  format      Format code"

# Development commands
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	npm install

dev:
	@echo "Starting development environment..."
	docker-compose up -d opensearch opensearch-dashboards
	@echo "Waiting for OpenSearch to be ready..."
	@sleep 30
	python src/main.py

test:
	@echo "Running tests..."
	pytest tests/ -v --cov=src --cov-report=html --cov-report=xml

clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml

# Production commands
prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.prod.yml up -d

deploy:
	@echo "Deploying to production..."
	./scripts/deploy.sh

backup:
	@echo "Creating backup..."
	./scripts/deploy.sh -b

restore:
	@echo "Restoring from backup..."
	@read -p "Enter backup date (YYYYMMDD_HHMMSS): " backup_date; \
	./scripts/restore.sh $$backup_date

# Monitoring commands
logs:
	@echo "Viewing logs..."
	docker-compose logs -f

logs-prod:
	@echo "Viewing production logs..."
	docker-compose -f docker-compose.prod.yml logs -f

status:
	@echo "Checking service status..."
	docker-compose ps

status-prod:
	@echo "Checking production service status..."
	docker-compose -f docker-compose.prod.yml ps

health:
	@echo "Checking health endpoints..."
	@echo "API Health:"
	@curl -s http://localhost:8000/api/health | jq . || echo "API not responding"
	@echo ""
	@echo "OpenSearch Health:"
	@curl -s http://localhost:9200/_cluster/health | jq . || echo "OpenSearch not responding"

# Utility commands
setup:
	@echo "Setting up Policy Pilot..."
	@echo "1. Creating directories..."
	mkdir -p uploads data logs models backups nginx/ssl
	@echo "2. Copying environment file..."
	@if [ ! -f .env ]; then cp env.prod.example .env; fi
	@echo "3. Installing dependencies..."
	make install
	@echo "4. Starting services..."
	make dev
	@echo "Setup complete! Check http://localhost:8000/docs for API documentation"

update:
	@echo "Updating dependencies..."
	pip install --upgrade -r requirements.txt
	npm update

lint:
	@echo "Running linting..."
	flake8 src/
	black --check src/
	isort --check-only src/

format:
	@echo "Formatting code..."
	black src/
	isort src/

# Docker commands
build:
	@echo "Building Docker images..."
	docker-compose build

build-prod:
	@echo "Building production Docker images..."
	docker-compose -f docker-compose.prod.yml build

stop:
	@echo "Stopping services..."
	docker-compose down

stop-prod:
	@echo "Stopping production services..."
	docker-compose -f docker-compose.prod.yml down

restart:
	@echo "Restarting services..."
	docker-compose restart

restart-prod:
	@echo "Restarting production services..."
	docker-compose -f docker-compose.prod.yml restart

# Database commands
db-reset:
	@echo "Resetting database..."
	docker-compose down -v
	docker-compose up -d opensearch
	@echo "Waiting for OpenSearch to be ready..."
	@sleep 30

db-backup:
	@echo "Backing up database..."
	docker exec policy-pilot-opensearch-prod curl -X POST "localhost:9200/_snapshot/backup_repo/snapshot_$(shell date +%Y%m%d_%H%M%S)?wait_for_completion=true"

# Security commands
ssl-setup:
	@echo "Setting up SSL certificates..."
	@echo "Please place your SSL certificates in nginx/ssl/"
	@echo "Required files: cert.pem, key.pem"

# Performance commands
benchmark:
	@echo "Running performance benchmark..."
	python scripts/benchmark.py

load-test:
	@echo "Running load test..."
	python scripts/load_test.py

# Documentation commands
docs:
	@echo "Generating documentation..."
	python -m pydoc -w src/
	@echo "Documentation generated in current directory"

# Maintenance commands
maintenance:
	@echo "Running maintenance tasks..."
	@echo "1. Cleaning old logs..."
	find logs/ -name "*.log" -mtime +30 -delete
	@echo "2. Cleaning old backups..."
	find backups/ -name "backup_*" -mtime +7 -delete
	@echo "3. Optimizing database..."
	docker exec policy-pilot-opensearch-prod curl -X POST "localhost:9200/_forcemerge?max_num_segments=1"
	@echo "Maintenance complete"

# Quick start commands
quick-start:
	@echo "Quick start - Policy Pilot"
	@echo "1. Starting OpenSearch..."
	docker-compose up -d opensearch opensearch-dashboards
	@echo "2. Waiting for services..."
	@sleep 30
	@echo "3. Starting API..."
	python src/main.py &
	@echo "4. Services started!"
	@echo "   - API: http://localhost:8000"
	@echo "   - Docs: http://localhost:8000/docs"
	@echo "   - OpenSearch: http://localhost:9200"
	@echo "   - Dashboards: http://localhost:5601"

# Emergency commands
emergency-stop:
	@echo "Emergency stop - stopping all services..."
	docker-compose down
	docker-compose -f docker-compose.prod.yml down
	docker stop $(docker ps -q) 2>/dev/null || true

emergency-clean:
	@echo "Emergency clean - removing all containers and volumes..."
	docker-compose down -v
	docker-compose -f docker-compose.prod.yml down -v
	docker system prune -f
	docker volume prune -f