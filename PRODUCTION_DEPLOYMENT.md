# Production Deployment Guide

This guide provides comprehensive instructions for deploying Policy Pilot RAG backend to production.

## Prerequisites

- Docker and Docker Compose
- OpenSearch cluster (or single node)
- OpenAI API key
- Domain name and SSL certificates (for production)
- Monitoring and logging infrastructure

## Environment Configuration

### 1. Environment Variables

Create `.env.production` file:

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
WORKERS=4

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=["https://policypilot.ai", "https://www.policypilot.ai"]

# OpenSearch
OPENSEARCH_URL=https://opensearch:9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=your-opensearch-password
OPENSEARCH_INDEX=policy_documents_prod

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=3

# File Upload
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_DIR=/app/uploads
DATA_DIR=/app/data

# Caching
CACHE_TTL=3600
CACHE_MAX_SIZE=10000

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=10

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/policy_pilot.log
LOG_FORMAT=json

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# Performance
EMBEDDING_BATCH_SIZE=64
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=300

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Health Checks
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
```

### 2. Docker Compose Production

Use `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.production
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      - opensearch
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  opensearch:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - discovery.type=single-node
      - "OPENSEARCH_INITIAL_ADMIN_PASSWORD=your-opensearch-password"
      - "DISABLE_INSTALL_DEMO_CONFIG=true"
      - "DISABLE_SECURITY_PLUGIN=false"
    ports:
      - "9200:9200"
      - "9600:9600"
    volumes:
      - opensearch-data:/usr/share/opensearch/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  opensearch-data:
```

## Security Configuration

### 1. SSL/TLS Setup

1. Obtain SSL certificates from a trusted CA
2. Place certificates in `nginx/ssl/` directory
3. Update nginx configuration for HTTPS

### 2. Firewall Configuration

```bash
# Allow only necessary ports
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

### 3. Security Headers

Configure nginx with security headers:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'" always;
```

## Monitoring and Logging

### 1. Application Metrics

The application exposes metrics at `/api/metrics`:

- Performance metrics
- System resource usage
- Cache statistics
- API request metrics

### 2. Health Checks

Multiple health check endpoints:

- `/api/health` - Basic health check
- `/api/health/ready` - Readiness probe
- `/api/health/live` - Liveness probe
- `/api/health/services` - Service-specific health

### 3. Logging

Structured JSON logging with:

- Request/response logging
- Error tracking with unique IDs
- Performance metrics
- Security events

### 4. Monitoring Stack

Recommended monitoring tools:

- **Prometheus** for metrics collection
- **Grafana** for visualization
- **ELK Stack** for log aggregation
- **AlertManager** for alerting

## Performance Optimization

### 1. Resource Limits

Set appropriate resource limits:

```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

### 2. Caching Strategy

- Search results cached for 5 minutes
- GPT responses cached for 1 hour (non-RAG only)
- Document embeddings cached in memory

### 3. Database Optimization

- OpenSearch cluster with multiple nodes
- Proper index mapping and settings
- Regular index optimization

## Backup and Recovery

### 1. Data Backup

```bash
# Backup OpenSearch data
curl -X POST "localhost:9200/_snapshot/backup_repo/snapshot_1"

# Backup application data
tar -czf backup_$(date +%Y%m%d).tar.gz uploads/ data/ logs/
```

### 2. Recovery Procedures

1. Restore OpenSearch from snapshot
2. Restore application data
3. Restart services
4. Verify health checks

## Scaling

### 1. Horizontal Scaling

- Use load balancer (nginx/HAProxy)
- Scale application containers
- Use OpenSearch cluster

### 2. Vertical Scaling

- Increase container resources
- Optimize embedding batch sizes
- Tune JVM settings for OpenSearch

## Maintenance

### 1. Regular Tasks

- Monitor disk space and logs
- Update dependencies
- Review security patches
- Backup data regularly

### 2. Updates

1. Test updates in staging
2. Backup production data
3. Deploy with zero-downtime strategy
4. Monitor for issues

## Troubleshooting

### 1. Common Issues

- **High memory usage**: Check embedding batch size
- **Slow queries**: Review OpenSearch performance
- **Rate limiting**: Adjust rate limits
- **File upload errors**: Check file size limits

### 2. Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG
```

### 3. Health Check Failures

Check individual services:

```bash
curl http://localhost:8000/api/health/services
```

## Security Checklist

- [ ] SSL/TLS certificates configured
- [ ] Firewall rules applied
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Input validation enabled
- [ ] Error messages sanitized
- [ ] Logs don't contain sensitive data
- [ ] Regular security updates
- [ ] Access controls in place
- [ ] Backup encryption enabled

## Performance Checklist

- [ ] Resource limits set
- [ ] Caching enabled
- [ ] Database optimized
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Load testing completed
- [ ] Backup procedures tested
- [ ] Recovery procedures documented

## Support

For production support:

1. Check application logs
2. Review metrics and alerts
3. Verify health checks
4. Check system resources
5. Review recent changes

Contact the development team with:
- Error IDs from logs
- Relevant metrics
- Steps to reproduce issues
- System information
