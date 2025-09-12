"""
Custom exception classes for Policy Pilot RAG backend.
All exceptions inherit from the base PolicyPilotException.
"""


class PolicyPilotException(Exception):
    """Base exception class for all Policy Pilot exceptions."""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class DocumentProcessingError(PolicyPilotException):
    """Raised when document processing fails."""
    pass


class SearchServiceError(PolicyPilotException):
    """Raised when search service operations fail."""
    pass


class EmbeddingServiceError(PolicyPilotException):
    """Raised when embedding generation fails."""
    pass


class GPTServiceError(PolicyPilotException):
    """Raised when GPT API calls fail."""
    pass


class ValidationError(PolicyPilotException):
    """Raised when input validation fails."""
    pass


class FileUploadError(PolicyPilotException):
    """Raised when file upload operations fail."""
    pass


class OpenSearchError(PolicyPilotException):
    """Raised when OpenSearch operations fail."""
    pass


class ConfigurationError(PolicyPilotException):
    """Raised when configuration is invalid or missing."""
    pass
