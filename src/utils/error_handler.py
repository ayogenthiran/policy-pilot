"""
Enhanced error handling for Policy Pilot RAG backend.
Provides comprehensive error messages and sanitization.
"""

import traceback
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.logging import get_logger
from src.utils.exceptions import PolicyPilotException
from src.utils.security import security_validator

logger = get_logger(__name__)


class ErrorHandler:
    """Enhanced error handler with sanitization and logging."""
    
    def __init__(self):
        """Initialize error handler."""
        self.logger = get_logger(__name__)
    
    def sanitize_error_message(self, error: Exception, include_details: bool = False) -> str:
        """
        Sanitize error message for user consumption.
        
        Args:
            error: Exception to sanitize
            include_details: Whether to include technical details
            
        Returns:
            Sanitized error message
        """
        try:
            # Get base error message
            if isinstance(error, PolicyPilotException):
                message = error.message
            elif isinstance(error, HTTPException):
                message = str(error.detail)
            else:
                message = str(error)
            
            # Sanitize the message
            sanitized = security_validator.sanitize_text(message)
            
            # Truncate if too long
            if len(sanitized) > 500:
                sanitized = sanitized[:500] + "..."
            
            # Add generic message if sanitization removed everything
            if not sanitized.strip():
                sanitized = "An error occurred while processing your request."
            
            # Add technical details if requested and safe
            if include_details and isinstance(error, PolicyPilotException) and error.details:
                details = security_validator.sanitize_text(error.details)
                if details and len(details) < 200:
                    sanitized += f" Details: {details}"
            
            return sanitized
            
        except Exception as e:
            self.logger.error(f"Failed to sanitize error message: {e}")
            return "An error occurred while processing your request."
    
    def get_error_response(self, error: Exception, request: Optional[Request] = None) -> Dict[str, Any]:
        """
        Get standardized error response.
        
        Args:
            error: Exception that occurred
            request: FastAPI request object
            
        Returns:
            Standardized error response
        """
        try:
            # Determine error type and status code
            if isinstance(error, HTTPException):
                status_code = error.status_code
                error_type = "http_error"
            elif isinstance(error, RequestValidationError):
                status_code = 422
                error_type = "validation_error"
            elif isinstance(error, PolicyPilotException):
                status_code = self._get_policy_pilot_status_code(error)
                error_type = "policy_pilot_error"
            else:
                status_code = 500
                error_type = "internal_error"
            
            # Create error ID for tracking
            error_id = self._generate_error_id()
            
            # Sanitize error message
            sanitized_message = self.sanitize_error_message(error, include_details=False)
            
            # Log error with context
            self._log_error(error, error_id, request)
            
            # Create response
            response = {
                "error": True,
                "error_id": error_id,
                "message": sanitized_message,
                "type": error_type,
                "status_code": status_code
            }
            
            # Add validation details for validation errors
            if isinstance(error, RequestValidationError):
                response["validation_errors"] = self._format_validation_errors(error)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to create error response: {e}")
            return {
                "error": True,
                "error_id": "unknown",
                "message": "An error occurred while processing your request.",
                "type": "internal_error",
                "status_code": 500
            }
    
    def _get_policy_pilot_status_code(self, error: PolicyPilotException) -> int:
        """
        Get HTTP status code for PolicyPilotException.
        
        Args:
            error: PolicyPilotException
            
        Returns:
            HTTP status code
        """
        # Map exception types to status codes
        status_map = {
            "ValidationError": 400,
            "FileUploadError": 400,
            "DocumentProcessingError": 422,
            "SearchServiceError": 503,
            "EmbeddingServiceError": 503,
            "GPTServiceError": 503,
            "OpenSearchError": 503,
            "ConfigurationError": 500
        }
        
        return status_map.get(type(error).__name__, 500)
    
    def _generate_error_id(self) -> str:
        """
        Generate unique error ID for tracking.
        
        Returns:
            Unique error ID
        """
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _log_error(self, error: Exception, error_id: str, request: Optional[Request] = None) -> None:
        """
        Log error with context.
        
        Args:
            error: Exception that occurred
            error_id: Unique error ID
            request: FastAPI request object
        """
        try:
            # Prepare log context
            log_context = {
                "error_id": error_id,
                "error_type": type(error).__name__,
                "error_message": str(error)
            }
            
            # Add request context if available
            if request:
                log_context.update({
                    "method": request.method,
                    "url": str(request.url),
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent")
                })
            
            # Add traceback for internal errors
            if not isinstance(error, (HTTPException, RequestValidationError)):
                log_context["traceback"] = traceback.format_exc()
            
            # Log based on error severity
            if isinstance(error, HTTPException) and error.status_code < 500:
                self.logger.warning(f"Client error {error_id}: {error}", extra=log_context)
            else:
                self.logger.error(f"Server error {error_id}: {error}", extra=log_context)
                
        except Exception as e:
            self.logger.error(f"Failed to log error: {e}")
    
    def _format_validation_errors(self, error: RequestValidationError) -> list:
        """
        Format validation errors for response.
        
        Args:
            error: RequestValidationError
            
        Returns:
            Formatted validation errors
        """
        try:
            formatted_errors = []
            
            for err in error.errors():
                formatted_errors.append({
                    "field": " -> ".join(str(loc) for loc in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"]
                })
            
            return formatted_errors
            
        except Exception as e:
            self.logger.error(f"Failed to format validation errors: {e}")
            return [{"field": "unknown", "message": "Validation error", "type": "unknown"}]


# Global error handler instance
error_handler = ErrorHandler()


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for FastAPI.
    
    Args:
        request: FastAPI request object
        exc: Exception that occurred
        
    Returns:
        JSON error response
    """
    try:
        # Get error response
        error_response = error_handler.get_error_response(exc, request)
        
        # Return JSON response
        return JSONResponse(
            status_code=error_response["status_code"],
            content=error_response
        )
        
    except Exception as e:
        logger.error(f"Failed to handle exception: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "error_id": "handler_error",
                "message": "An error occurred while processing your request.",
                "type": "internal_error",
                "status_code": 500
            }
        )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP exception handler for FastAPI.
    
    Args:
        request: FastAPI request object
        exc: HTTPException that occurred
        
    Returns:
        JSON error response
    """
    try:
        # Get error response
        error_response = error_handler.get_error_response(exc, request)
        
        # Return JSON response
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
        
    except Exception as e:
        logger.error(f"Failed to handle HTTP exception: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "error_id": "handler_error",
                "message": "An error occurred while processing your request.",
                "type": "internal_error",
                "status_code": 500
            }
        )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Validation exception handler for FastAPI.
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError that occurred
        
    Returns:
        JSON error response
    """
    try:
        # Get error response
        error_response = error_handler.get_error_response(exc, request)
        
        # Return JSON response
        return JSONResponse(
            status_code=422,
            content=error_response
        )
        
    except Exception as e:
        logger.error(f"Failed to handle validation exception: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "error_id": "handler_error",
                "message": "An error occurred while processing your request.",
                "type": "internal_error",
                "status_code": 500
            }
        )
