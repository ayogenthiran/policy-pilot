"""
Main FastAPI application for Policy Pilot RAG backend.
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from src.config.settings import settings
from src.core.logging import get_logger
from src.api.middleware import add_cors_middleware, add_exception_handlers
from src.api.routes import documents, query, health
from src.api.rate_limiter import rate_limit_middleware
from src.utils.metrics import metrics_collector, structured_logger
from src.utils.security import security_validator
from src.utils.error_handler import (
    global_exception_handler, 
    http_exception_handler, 
    validation_exception_handler
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Policy Pilot API starting up...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"API Host: {settings.api_host}:{settings.api_port}")
    
    # Initialize services
    try:
        from src.services.rag_service import RAGService
        from src.config.database import opensearch_connection
        
        # Test OpenSearch connection
        opensearch_health = opensearch_connection.health_check()
        logger.info(f"OpenSearch connection: {opensearch_health['status']}")
        
        # Initialize RAG service
        rag_service = RAGService()
        
        # Check system health
        health_status = rag_service.get_system_health()
        logger.info(f"System health check: {health_status['status']}")
        
        if health_status['status'] != 'healthy':
            logger.warning("System health check failed - some services may not be available")
            logger.warning(f"Service statuses: {health_status['services']}")
        else:
            logger.info("All services are healthy and ready")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        logger.error("Application will start but some features may not be available")
    
    yield
    
    # Shutdown
    logger.info("Policy Pilot API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Policy Pilot API",
    description="A comprehensive RAG (Retrieval-Augmented Generation) system for policy document analysis and intelligent query answering",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "Policy Pilot Team",
        "email": "support@policypilot.ai",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": f"http://{settings.api_host}:{settings.api_port}",
            "description": "Development server"
        },
        {
            "url": "https://api.policypilot.ai",
            "description": "Production server"
        }
    ]
)

# Add CORS middleware
add_cors_middleware(app, settings.cors_origins)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Add performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Middleware for performance monitoring."""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Record metrics
    metrics_collector.record_metric(
        operation="api_request",
        duration=duration,
        success=200 <= response.status_code < 400,
        metadata={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": request.client.host if request.client else None
        }
    )
    
    # Log structured request
    structured_logger.log_api_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration,
        client_ip=request.client.host if request.client else None
    )
    
    return response

# Add enhanced exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include routers
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(health.router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Policy Pilot API",
        "version": "1.0.0",
        "status": "running",
        "description": "A comprehensive RAG system for policy document analysis",
        "features": [
            "Document upload and processing",
            "Intelligent query answering",
            "Semantic search capabilities",
            "Multi-format document support",
            "Real-time health monitoring"
        ],
        "endpoints": {
            "documentation": "/docs",
            "health": "/api/health",
            "documents": "/api/documents",
            "query": "/api/query",
            "search": "/api/search"
        },
        "environment": os.getenv('ENVIRONMENT', 'development')
    }


@app.get("/api", tags=["root"])
async def api_root():
    """API root endpoint with detailed information."""
    return {
        "message": "Policy Pilot RAG API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "documents": {
                "upload": "POST /api/upload-document",
                "list": "GET /api/documents",
                "get": "GET /api/documents/{id}",
                "delete": "DELETE /api/documents/{id}",
                "chunks": "GET /api/documents/{id}/chunks",
                "stats": "GET /api/documents/stats"
            },
            "query": {
                "query": "POST /api/query",
                "search": "POST /api/search",
                "simple_query": "GET /api/query/simple",
                "simple_search": "GET /api/search/simple",
                "test": "POST /api/query/test"
            },
            "health": {
                "health": "GET /api/health",
                "system_info": "GET /api/system-info",
                "opensearch": "GET /api/health/opensearch",
                "services": "GET /api/health/services",
                "ready": "GET /api/health/ready",
                "live": "GET /api/health/live"
            }
        },
        "documentation": "/docs",
        "openapi_spec": "/openapi.json"
    }


@app.get("/api/status", tags=["root"])
async def api_status():
    """API status endpoint for monitoring."""
    try:
        from src.services.rag_service import RAGService
        rag_service = RAGService()
        health_status = rag_service.get_system_health()
        
        return {
            "status": "operational" if health_status['status'] == 'healthy' else "degraded",
            "timestamp": health_status['timestamp'],
            "services": {
                service: status['status'] 
                for service, status in health_status['services'].items()
            },
            "uptime": "N/A",  # Would be calculated in production
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "version": "1.0.0"
        }


@app.get("/api/metrics", tags=["monitoring"])
async def get_metrics():
    """Get application metrics."""
    try:
        from src.utils.metrics import system_monitor
        from src.services.cache_service import cache_service
        
        # Get performance metrics
        performance_metrics = metrics_collector.get_metrics_summary()
        
        # Get system metrics
        system_metrics = system_monitor.get_system_metrics()
        
        # Get cache metrics
        cache_metrics = cache_service.get_stats()
        
        return {
            "performance": performance_metrics,
            "system": {
                "cpu_percent": system_metrics.cpu_percent,
                "memory_percent": system_metrics.memory_percent,
                "memory_available_gb": system_metrics.memory_available_gb,
                "disk_usage_percent": system_metrics.disk_usage_percent
            },
            "cache": cache_metrics,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {
            "error": str(e),
            "timestamp": time.time()
        }


if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": settings.log_level.upper(),
            "handlers": ["default"],
        },
    }
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
        access_log=True,
        log_config=log_config
    )
