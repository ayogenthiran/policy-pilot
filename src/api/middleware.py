"""
FastAPI middleware for Policy Pilot RAG backend.
Handles CORS configuration and global exception handling.
"""

from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.logging import get_logger
from src.utils.exceptions import (
    PolicyPilotException,
    DocumentProcessingError,
    SearchServiceError,
    EmbeddingServiceError,
    GPTServiceError,
    ValidationError,
    FileUploadError,
    OpenSearchError,
    ConfigurationError
)
from src.models.schemas import ErrorResponse

logger = get_logger(__name__)


def add_cors_middleware(app: FastAPI, cors_origins: list) -> None:
    """
    Add CORS middleware to FastAPI application.
    
    Args:
        app: FastAPI application instance
        cors_origins: List of allowed CORS origins
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    logger.info(f"CORS middleware added with origins: {cors_origins}")


def add_exception_handlers(app: FastAPI) -> None:
    """
    Add global exception handlers to FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(PolicyPilotException)
    async def policy_pilot_exception_handler(request: Request, exc: PolicyPilotException) -> JSONResponse:
        """Handle PolicyPilot custom exceptions."""
        logger.error(f"PolicyPilot exception: {exc.message} - {exc.details}")
        
        error_response = ErrorResponse(
            success=False,
            message=exc.message,
            error_code=exc.__class__.__name__,
            error_details={"details": exc.details} if exc.details else None
        )
        
        return JSONResponse(
            status_code=400,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(DocumentProcessingError)
    async def document_processing_exception_handler(request: Request, exc: DocumentProcessingError) -> JSONResponse:
        """Handle document processing errors."""
        logger.error(f"Document processing error: {exc.message}")
        
        error_response = ErrorResponse(
            success=False,
            message=f"Document processing failed: {exc.message}",
            error_code="DOCUMENT_PROCESSING_ERROR",
            error_details={"details": exc.details} if exc.details else None
        )
        
        return JSONResponse(
            status_code=422,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(FileUploadError)
    async def file_upload_exception_handler(request: Request, exc: FileUploadError) -> JSONResponse:
        """Handle file upload errors."""
        logger.error(f"File upload error: {exc.message}")
        
        error_response = ErrorResponse(
            success=False,
            message=f"File upload failed: {exc.message}",
            error_code="FILE_UPLOAD_ERROR",
            error_details={"details": exc.details} if exc.details else None
        )
        
        return JSONResponse(
            status_code=400,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle validation errors."""
        logger.error(f"Validation error: {exc.message}")
        
        error_response = ErrorResponse(
            success=False,
            message=f"Validation failed: {exc.message}",
            error_code="VALIDATION_ERROR",
            error_details={"details": exc.details} if exc.details else None
        )
        
        return JSONResponse(
            status_code=422,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(SearchServiceError)
    async def search_service_exception_handler(request: Request, exc: SearchServiceError) -> JSONResponse:
        """Handle search service errors."""
        logger.error(f"Search service error: {exc.message}")
        
        error_response = ErrorResponse(
            success=False,
            message=f"Search service error: {exc.message}",
            error_code="SEARCH_SERVICE_ERROR",
            error_details={"details": exc.details} if exc.details else None
        )
        
        return JSONResponse(
            status_code=503,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(EmbeddingServiceError)
    async def embedding_service_exception_handler(request: Request, exc: EmbeddingServiceError) -> JSONResponse:
        """Handle embedding service errors."""
        logger.error(f"Embedding service error: {exc.message}")
        
        error_response = ErrorResponse(
            success=False,
            message=f"Embedding service error: {exc.message}",
            error_code="EMBEDDING_SERVICE_ERROR",
            error_details={"details": exc.details} if exc.details else None
        )
        
        return JSONResponse(
            status_code=503,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(GPTServiceError)
    async def gpt_service_exception_handler(request: Request, exc: GPTServiceError) -> JSONResponse:
        """Handle GPT service errors."""
        logger.error(f"GPT service error: {exc.message}")
        
        error_response = ErrorResponse(
            success=False,
            message=f"GPT service error: {exc.message}",
            error_code="GPT_SERVICE_ERROR",
            error_details={"details": exc.details} if exc.details else None
        )
        
        return JSONResponse(
            status_code=503,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(OpenSearchError)
    async def opensearch_exception_handler(request: Request, exc: OpenSearchError) -> JSONResponse:
        """Handle OpenSearch errors."""
        logger.error(f"OpenSearch error: {exc.message}")
        
        error_response = ErrorResponse(
            success=False,
            message=f"Database error: {exc.message}",
            error_code="DATABASE_ERROR",
            error_details={"details": exc.details} if exc.details else None
        )
        
        return JSONResponse(
            status_code=503,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(ConfigurationError)
    async def configuration_exception_handler(request: Request, exc: ConfigurationError) -> JSONResponse:
        """Handle configuration errors."""
        logger.error(f"Configuration error: {exc.message}")
        
        error_response = ErrorResponse(
            success=False,
            message=f"Configuration error: {exc.message}",
            error_code="CONFIGURATION_ERROR",
            error_details={"details": exc.details} if exc.details else None
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation errors."""
        logger.error(f"Request validation error: {exc.errors()}")
        
        error_response = ErrorResponse(
            success=False,
            message="Request validation failed",
            error_code="VALIDATION_ERROR",
            error_details={
                "validation_errors": exc.errors(),
                "body": exc.body
            }
        )
        
        return JSONResponse(
            status_code=422,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
        
        error_response = ErrorResponse(
            success=False,
            message=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}",
            error_details={"status_code": exc.status_code}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle general exceptions."""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        
        error_response = ErrorResponse(
            success=False,
            message="An unexpected error occurred",
            error_code="INTERNAL_SERVER_ERROR",
            error_details={"error_type": type(exc).__name__}
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump()
        )
    
    logger.info("Exception handlers added to FastAPI application")


def create_error_response(message: str, error_code: str, 
                         status_code: int = 400, 
                         details: Dict[str, Any] = None) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        error_code: Error code
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        JSONResponse with error information
    """
    error_response = ErrorResponse(
        success=False,
        message=message,
        error_code=error_code,
        error_details=details
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )
