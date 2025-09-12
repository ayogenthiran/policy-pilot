# Policy Pilot Deployment Guide

This guide covers production deployment of Policy Pilot using Docker, including environment configuration, scaling considerations, and monitoring setup.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Production Environment Setup](#production-environment-setup)
- [Docker Deployment](#docker-deployment)
- [Environment Configuration](#environment-configuration)
- [Scaling and Performance](#scaling-and-performance)
- [Monitoring and Logging](#monitoring-and-logging)
- [Security Considerations](#security-considerations)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 100GB SSD
- OS: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+

**Recommended Requirements:**
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 500GB+ SSD
- OS: Ubuntu 22.04 LTS

### Software Dependencies

- Docker 20.10+
- Docker Compose 2.0+
- Git
- curl/wget

### External Services

- OpenAI API account with sufficient credits
- Domain name (for production)
- SSL certificate (for HTTPS)

## Production Environment Setup

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 2. Create Application User

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash policypilot
sudo usermod -aG docker policypilot

# Switch to application user
sudo su - policypilot
```

### 3. Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-username/policy-pilot.git
cd policy-pilot

# Checkout production branch
git checkout production
```

## Docker Deployment

### 1. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  opensearch:
    image: opensearchproject/opensearch:2.11.0
    container_name: policy-pilot-opensearch-prod
    environment:
      - discovery.type=single-node
      - DISABLE_INSTALL_DEMO_CONFIG=true
      - DISABLE_SECURITY_PLUGIN=true
      - OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g
      - "OPENSEARCH_INITIAL_ADMIN_PASSWORD=${OPENSEARCH_PASSWORD}"
    ports:
      - "9200:9200"
      - "9600:9600"
    volumes:
      - opensearch_data:/usr/share/opensearch/data
      - ./opensearch/config:/usr/share/opensearch/config
    networks:
      - policy-pilot-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  opensearch-dashboards:
    image: opensearchproject/opensearch-dashboards:2.11.0
    container_name: policy-pilot-dashboards-prod
    environment:
      - OPENSEARCH_HOSTS=http://opensearch:9200
      - DISABLE_SECURITY_DASHBOARDS_PLUGIN=true
    ports:
      - "5601:5601"
    depends_on:
      opensearch:
        condition: service_healthy
    networks:
      - policy-pilot-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  policy-pilot-api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: policy-pilot-api-prod
    environment:
      - ENVIRONMENT=production
      - OPENSEARCH_URL=http://opensearch:9200
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - API_HOST=0.0.0.0
      - API_PORT=8000
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./data:/app/data
      - ./logs:/app/logs
      - ./models:/app/models
    depends_on:
      opensearch:
        condition: service_healthy
    networks:
      - policy-pilot-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/api/health/live || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  nginx:
    image: nginx:alpine
    container_name: policy-pilot-nginx-prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - policy-pilot-api
    networks:
      - policy-pilot-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: policy-pilot-redis-prod
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - policy-pilot-network
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru

volumes:
  opensearch_data:
    driver: local
  redis_data:
    driver: local

networks:
  policy-pilot-network:
    driver: bridge
```

### 2. Production Dockerfile

Create `Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY pyproject.toml .

# Create necessary directories
RUN mkdir -p uploads data logs models

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/live || exit 1

# Run the application
CMD ["python", "src/main.py"]
```

### 3. Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server policy-pilot-api:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=1r/s;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Client max body size for file uploads
        client_max_body_size 100M;

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # File upload endpoint with stricter rate limiting
        location /api/upload-document {
            limit_req zone=upload burst=5 nodelay;
            
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Extended timeouts for file uploads
            proxy_connect_timeout 120s;
            proxy_send_timeout 120s;
            proxy_read_timeout 120s;
        }

        # Health check endpoint
        location /api/health {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Logging
        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;
    }
}
```

## Environment Configuration

### 1. Production Environment File

Create `.env.prod`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_production_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# OpenSearch Configuration
OPENSEARCH_URL=http://opensearch:9200
OPENSEARCH_PASSWORD=your_secure_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=production

# CORS Configuration
CORS_ORIGINS=["https://your-domain.com", "https://www.your-domain.com"]

# Logging
LOG_LEVEL=INFO

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/policypilot

# Redis
REDIS_URL=redis://redis:6379/0

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
PROMETHEUS_ENABLED=true

# File Storage
MAX_FILE_SIZE=104857600  # 100MB
ALLOWED_FILE_TYPES=pdf,docx,txt,png,jpg,jpeg

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
UPLOAD_RATE_LIMIT_PER_MINUTE=10
```

### 2. Environment Validation

Create `scripts/validate-env.sh`:

```bash
#!/bin/bash

# Validate environment variables
validate_env() {
    local var_name=$1
    local var_value=$2
    
    if [ -z "$var_value" ]; then
        echo "Error: $var_name is not set"
        exit 1
    fi
}

# Required variables
validate_env "OPENAI_API_KEY" "$OPENAI_API_KEY"
validate_env "OPENSEARCH_PASSWORD" "$OPENSEARCH_PASSWORD"
validate_env "SECRET_KEY" "$SECRET_KEY"

echo "Environment validation passed"
```

## Scaling and Performance

### 1. Horizontal Scaling

For high-traffic deployments, consider:

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  policy-pilot-api:
    # ... existing configuration
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  nginx:
    # ... existing configuration
    depends_on:
      - policy-pilot-api
```

### 2. Load Balancing

Use multiple API instances with load balancing:

```bash
# Scale API service
docker-compose -f docker-compose.prod.yml up -d --scale policy-pilot-api=3
```

### 3. Database Optimization

**OpenSearch Configuration:**

```yaml
# opensearch/config/opensearch.yml
cluster.name: policy-pilot-cluster
node.name: policy-pilot-node-1
network.host: 0.0.0.0
discovery.type: single-node

# Performance settings
indices.memory.index_buffer_size: 20%
indices.queries.cache.size: 10%
indices.fielddata.cache.size: 20%

# Thread pool settings
thread_pool:
  search:
    size: 8
    queue_size: 1000
  write:
    size: 4
    queue_size: 200
```

### 4. Caching Strategy

**Redis Configuration:**

```bash
# Redis configuration for caching
redis-server --appendonly yes \
  --maxmemory 2gb \
  --maxmemory-policy allkeys-lru \
  --save 900 1 \
  --save 300 10 \
  --save 60 10000
```

## Monitoring and Logging

### 1. Log Management

**Structured Logging Configuration:**

```python
# src/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
            
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)
```

### 2. Health Monitoring

**Prometheus Metrics:**

```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Business metrics
DOCUMENTS_PROCESSED = Counter('documents_processed_total', 'Total documents processed')
QUERIES_PROCESSED = Counter('queries_processed_total', 'Total queries processed')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active database connections')

# System metrics
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')
```

### 3. Alerting

**Alert Rules (Prometheus):**

```yaml
# monitoring/alert-rules.yml
groups:
  - name: policy-pilot
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          
      - alert: ServiceDown
        expr: up{job="policy-pilot-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Policy Pilot API is down"
```

### 4. Log Aggregation

**ELK Stack Configuration:**

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
    driver: local
```

## Security Considerations

### 1. Network Security

```bash
# Firewall configuration
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. Container Security

```dockerfile
# Use non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Remove unnecessary packages
RUN apt-get autoremove -y && apt-get clean
```

### 3. Secrets Management

```bash
# Use Docker secrets
echo "your_openai_api_key" | docker secret create openai_api_key -
echo "your_opensearch_password" | docker secret create opensearch_password -
```

### 4. SSL/TLS Configuration

```bash
# Generate SSL certificate with Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

## Backup and Recovery

### 1. Data Backup

**Backup Script:**

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups/policy-pilot"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup OpenSearch data
docker exec policy-pilot-opensearch-prod \
  curl -X POST "localhost:9200/_snapshot/backup_repo/snapshot_$DATE?wait_for_completion=true"

# Backup application data
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz uploads/
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 2. Disaster Recovery

**Recovery Script:**

```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_DATE=$1
BACKUP_DIR="/backups/policy-pilot"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    exit 1
fi

# Restore OpenSearch data
docker exec policy-pilot-opensearch-prod \
  curl -X POST "localhost:9200/_snapshot/backup_repo/snapshot_$BACKUP_DATE/_restore"

# Restore application data
tar -xzf $BACKUP_DIR/uploads_$BACKUP_DATE.tar.gz
tar -xzf $BACKUP_DIR/logs_$BACKUP_DATE.tar.gz
```

## Troubleshooting

### 1. Common Issues

**Service Won't Start:**
```bash
# Check logs
docker-compose logs policy-pilot-api

# Check resource usage
docker stats

# Check disk space
df -h
```

**OpenSearch Connection Issues:**
```bash
# Check OpenSearch health
curl http://localhost:9200/_cluster/health

# Check OpenSearch logs
docker-compose logs opensearch
```

**Memory Issues:**
```bash
# Check memory usage
free -h
docker stats

# Increase memory limits in docker-compose.yml
```

### 2. Performance Tuning

**OpenSearch Tuning:**
```yaml
# opensearch/config/jvm.options
-Xms2g
-Xmx2g
-XX:+UseG1GC
-XX:G1HeapRegionSize=16m
```

**Application Tuning:**
```python
# src/config/settings.py
class Settings:
    # Increase worker processes
    WORKERS = 4
    
    # Increase connection pool size
    OPENSEARCH_POOL_SIZE = 20
    
    # Enable connection pooling
    OPENSEARCH_POOL_RECYCLE = 3600
```

### 3. Monitoring Commands

```bash
# Check service status
docker-compose ps

# Check resource usage
docker stats

# Check logs
docker-compose logs -f policy-pilot-api

# Check health endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/health/ready
curl http://localhost:8000/api/health/live
```

## Maintenance

### 1. Regular Maintenance

**Daily Tasks:**
- Check service health
- Monitor disk space
- Review error logs

**Weekly Tasks:**
- Update dependencies
- Clean old logs
- Backup data

**Monthly Tasks:**
- Security updates
- Performance review
- Capacity planning

### 2. Updates

**Application Updates:**
```bash
# Pull latest changes
git pull origin production

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Verify deployment
curl http://localhost:8000/api/health
```

**System Updates:**
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker
sudo apt install docker-ce docker-ce-cli containerd.io
```

## Support

For deployment support:
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/policy-pilot/issues)
- **Email**: deployment-support@policypilot.ai
