"""
Health check API routes for Policy Pilot RAG backend.
Handles system health monitoring and diagnostics.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.core.logging import get_logger
from src.services.rag_service import RAGService
from src.config.database import opensearch_connection
from src.models.query import HealthResponse, ComponentStatus
from src.models.schemas import HealthCheckResponse, SystemInfoResponse

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["health"])


def get_rag_service() -> RAGService:
    """Dependency to get RAG service instance."""
    return RAGService()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="System health check",
    description="Check the overall health status of the system"
)
async def health_check(
    rag_service: RAGService = Depends(get_rag_service)
) -> HealthCheckResponse:
    """
    Check the overall health status of the system.
    
    Args:
        rag_service: RAG service dependency
        
    Returns:
        System health status
    """
    try:
        # Get comprehensive system health
        system_health = rag_service.get_system_health()
        
        # Determine overall status
        overall_status = system_health['status']
        
        # Create health response
        health_response = HealthResponse(
            status=overall_status,
            components={
                "embedding_service": system_health['services']['embedding_service']['status'],
                "search_service": system_health['services']['search_service']['status'],
                "gpt_service": system_health['services']['gpt_service']['status'],
                "opensearch_connection": system_health['services']['opensearch_connection']['status'],
                "document_processor": system_health['services']['document_processor']['status']
            },
            details={
                "timestamp": system_health['timestamp'],
                "statistics": system_health['statistics'],
                "configuration": system_health['configuration']
            }
        )
        
        # Create API response
        api_response = HealthCheckResponse(
            success=overall_status == 'healthy',
            message=f"System health check completed - Status: {overall_status}",
            health=health_response
        )
        
        logger.info(f"Health check completed: {overall_status}")
        return api_response
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get(
    "/system-info",
    response_model=SystemInfoResponse,
    summary="System information",
    description="Get detailed system information and statistics"
)
async def system_info(
    rag_service: RAGService = Depends(get_rag_service)
) -> SystemInfoResponse:
    """
    Get detailed system information and statistics.
    
    Args:
        rag_service: RAG service dependency
        
    Returns:
        Detailed system information
    """
    try:
        # Get system health
        system_health = rag_service.get_system_health()
        
        # Get document statistics
        doc_stats = rag_service.get_document_statistics()
        
        # Create system info
        system_info = {
            "system_status": system_health['status'],
            "services": {
                "embedding_service": ComponentStatus(system_health['services']['embedding_service']['status']),
                "search_service": ComponentStatus(system_health['services']['search_service']['status']),
                "gpt_service": ComponentStatus(system_health['services']['gpt_service']['status']),
                "opensearch_connection": ComponentStatus(system_health['services']['opensearch_connection']['status']),
                "document_processor": ComponentStatus(system_health['services']['document_processor']['status'])
            },
            "configuration": system_health['configuration'],
            "statistics": {
                **system_health['statistics'],
                **doc_stats.get('documents', {})
            }
        }
        
        # Create API response
        api_response = SystemInfoResponse(
            success=True,
            message="System information retrieved successfully",
            system_info=system_info
        )
        
        return api_response
        
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system information")


@router.get(
    "/health/opensearch",
    summary="OpenSearch health check",
    description="Check the health status of OpenSearch connection"
)
async def opensearch_health() -> JSONResponse:
    """
    Check OpenSearch connection health.
    
    Returns:
        OpenSearch health status
    """
    try:
        # Get OpenSearch health
        opensearch_health = opensearch_connection.health_check()
        
        response = {
            "success": opensearch_health['status'] == 'healthy',
            "message": f"OpenSearch health check completed - Status: {opensearch_health['status']}",
            "opensearch_health": opensearch_health
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"OpenSearch health check failed: {e}")
        raise HTTPException(status_code=500, detail="OpenSearch health check failed")


@router.get(
    "/health/services",
    summary="Services health check",
    description="Check the health status of all individual services"
)
async def services_health(
    rag_service: RAGService = Depends(get_rag_service)
) -> JSONResponse:
    """
    Check the health status of all individual services.
    
    Args:
        rag_service: RAG service dependency
        
    Returns:
        Services health status
    """
    try:
        # Get system health
        system_health = rag_service.get_system_health()
        
        # Extract service health information
        services_health = {}
        for service_name, service_health in system_health['services'].items():
            services_health[service_name] = {
                "status": service_health['status'],
                "healthy": service_health['status'] == 'healthy',
                "details": service_health
            }
        
        # Determine overall services status
        all_healthy = all(
            service['healthy'] for service in services_health.values()
        )
        
        response = {
            "success": all_healthy,
            "message": f"Services health check completed - All healthy: {all_healthy}",
            "services": services_health,
            "overall_status": "healthy" if all_healthy else "degraded"
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Services health check failed: {e}")
        raise HTTPException(status_code=500, detail="Services health check failed")


@router.get(
    "/health/detailed",
    summary="Detailed health check",
    description="Get detailed health information for all system components"
)
async def detailed_health_check(
    rag_service: RAGService = Depends(get_rag_service)
) -> JSONResponse:
    """
    Get detailed health information for all system components.
    
    Args:
        rag_service: RAG service dependency
        
    Returns:
        Detailed health information
    """
    try:
        # Get comprehensive system health
        system_health = rag_service.get_system_health()
        
        # Get document statistics
        doc_stats = rag_service.get_document_statistics()
        
        # Create detailed response
        response = {
            "success": True,
            "message": "Detailed health check completed",
            "timestamp": system_health['timestamp'],
            "overall_status": system_health['status'],
            "components": {
                "embedding_service": {
                    "status": system_health['services']['embedding_service']['status'],
                    "model": system_health['statistics'].get('embedding_model', 'unknown'),
                    "healthy": system_health['services']['embedding_service']['status'] == 'healthy'
                },
                "search_service": {
                    "status": system_health['services']['search_service']['status'],
                    "index_name": system_health['statistics'].get('index_name', 'unknown'),
                    "healthy": system_health['services']['search_service']['status'] == 'healthy'
                },
                "gpt_service": {
                    "status": system_health['services']['gpt_service']['status'],
                    "model": system_health['statistics'].get('gpt_model', 'unknown'),
                    "healthy": system_health['services']['gpt_service']['status'] == 'healthy'
                },
                "opensearch_connection": {
                    "status": system_health['services']['opensearch_connection']['status'],
                    "url": system_health['configuration'].get('opensearch_url', 'unknown'),
                    "healthy": system_health['services']['opensearch_connection']['status'] == 'healthy'
                },
                "document_processor": {
                    "status": system_health['services']['document_processor']['status'],
                    "healthy": system_health['services']['document_processor']['status'] == 'healthy'
                }
            },
            "statistics": {
                **system_health['statistics'],
                **doc_stats.get('documents', {})
            },
            "configuration": system_health['configuration']
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail="Detailed health check failed")


@router.get(
    "/health/ready",
    summary="Readiness check",
    description="Check if the system is ready to accept requests"
)
async def readiness_check(
    rag_service: RAGService = Depends(get_rag_service)
) -> JSONResponse:
    """
    Check if the system is ready to accept requests.
    
    Args:
        rag_service: RAG service dependency
        
    Returns:
        Readiness status
    """
    try:
        # Get system health
        system_health = rag_service.get_system_health()
        
        # Check if critical services are healthy
        critical_services = ['embedding_service', 'search_service', 'gpt_service']
        critical_healthy = all(
            system_health['services'][service]['status'] == 'healthy'
            for service in critical_services
        )
        
        # Check if OpenSearch is accessible
        opensearch_healthy = system_health['services']['opensearch_connection']['status'] == 'healthy'
        
        # System is ready if critical services and OpenSearch are healthy
        ready = critical_healthy and opensearch_healthy
        
        response = {
            "success": ready,
            "message": "System ready" if ready else "System not ready",
            "ready": ready,
            "critical_services_healthy": critical_healthy,
            "opensearch_healthy": opensearch_healthy,
            "status": "ready" if ready else "not_ready"
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "Readiness check failed",
                "ready": False,
                "error": str(e)
            }
        )


@router.get(
    "/health/live",
    summary="Liveness check",
    description="Check if the system is alive and responding"
)
async def liveness_check() -> JSONResponse:
    """
    Check if the system is alive and responding.
    
    Returns:
        Liveness status
    """
    try:
        # Simple liveness check - just return success if we can respond
        response = {
            "success": True,
            "message": "System is alive",
            "alive": True,
            "status": "alive"
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Liveness check failed",
                "alive": False,
                "error": str(e)
            }
        )
