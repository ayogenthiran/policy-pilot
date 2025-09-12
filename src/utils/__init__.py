"""
Utility functions and classes for Policy Pilot RAG backend.

This package contains utility modules for the Policy Pilot RAG system,
including file handlers, text processing, and other helper functions.
"""

from .exceptions import (
    PolicyPilotException,
    DocumentProcessingError,
    SearchServiceError,
    EmbeddingServiceError,
    GPTServiceError,
    ValidationError,
    FileUploadError,
    OpenSearchError,
    ConfigurationError,
)

from .file_handlers import DocumentLoader
from .text_processing import TextChunker

__all__ = [
    # Exceptions
    "PolicyPilotException",
    "DocumentProcessingError",
    "SearchServiceError",
    "EmbeddingServiceError",
    "GPTServiceError",
    "ValidationError",
    "FileUploadError",
    "OpenSearchError",
    "ConfigurationError",
    
    # Utilities
    "DocumentLoader",
    "TextChunker",
]
