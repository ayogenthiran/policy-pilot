"""
Security utilities for Policy Pilot RAG backend.
Handles input validation, sanitization, and security checks.
"""

import re
import hashlib
import mimetypes
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import bleach
from urllib.parse import urlparse

from src.core.logging import get_logger
from src.utils.exceptions import ValidationError, SecurityError

logger = get_logger(__name__)


class SecurityValidator:
    """Service for input validation and sanitization."""
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.md', '.rtf'}
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Maximum text length
    MAX_TEXT_LENGTH = 100000
    
    # Maximum query length
    MAX_QUERY_LENGTH = 2000
    
    # Dangerous patterns
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'data:text/html',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\(',
        r'cmd\s*\/',
        r'powershell',
        r'bash\s*\-',
        r'sh\s*\-'
    ]
    
    def __init__(self):
        """Initialize the security validator."""
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS]
        logger.info("SecurityValidator initialized")
    
    def validate_file_upload(self, filename: str, file_size: int, 
                           content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate file upload for security.
        
        Args:
            filename: Name of the file
            file_size: Size of the file in bytes
            content_type: MIME type of the file
            
        Returns:
            Validation result with success status and details
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Check file size
            if file_size > self.MAX_FILE_SIZE:
                raise ValidationError(f"File size {file_size} exceeds maximum allowed size {self.MAX_FILE_SIZE}")
            
            # Check file extension
            file_path = Path(filename)
            extension = file_path.suffix.lower()
            if extension not in self.ALLOWED_EXTENSIONS:
                raise ValidationError(f"File extension {extension} is not allowed")
            
            # Check filename for dangerous characters
            if not self._is_safe_filename(filename):
                raise ValidationError("Filename contains potentially dangerous characters")
            
            # Validate content type if provided
            if content_type:
                expected_type = mimetypes.guess_type(filename)[0]
                if expected_type and content_type != expected_type:
                    logger.warning(f"Content type mismatch: {content_type} vs {expected_type}")
            
            return {
                'valid': True,
                'filename': filename,
                'file_size': file_size,
                'extension': extension,
                'content_type': content_type
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"File validation error: {e}")
            raise ValidationError(f"File validation failed: {e}")
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate search query for security.
        
        Args:
            query: Search query string
            
        Returns:
            Validation result with sanitized query
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Check query length
            if len(query) > self.MAX_QUERY_LENGTH:
                raise ValidationError(f"Query length {len(query)} exceeds maximum allowed length {self.MAX_QUERY_LENGTH}")
            
            # Check for empty query
            if not query or not query.strip():
                raise ValidationError("Query cannot be empty")
            
            # Sanitize query
            sanitized_query = self.sanitize_text(query)
            
            # Check for dangerous patterns
            if self._contains_dangerous_patterns(sanitized_query):
                raise ValidationError("Query contains potentially dangerous content")
            
            return {
                'valid': True,
                'original_query': query,
                'sanitized_query': sanitized_query,
                'length': len(sanitized_query)
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Query validation error: {e}")
            raise ValidationError(f"Query validation failed: {e}")
    
    def validate_text_input(self, text: str, max_length: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate text input for security.
        
        Args:
            text: Text to validate
            max_length: Maximum allowed length
            
        Returns:
            Validation result with sanitized text
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            max_len = max_length or self.MAX_TEXT_LENGTH
            
            # Check text length
            if len(text) > max_len:
                raise ValidationError(f"Text length {len(text)} exceeds maximum allowed length {max_len}")
            
            # Check for empty text
            if not text or not text.strip():
                raise ValidationError("Text cannot be empty")
            
            # Sanitize text
            sanitized_text = self.sanitize_text(text)
            
            # Check for dangerous patterns
            if self._contains_dangerous_patterns(sanitized_text):
                raise ValidationError("Text contains potentially dangerous content")
            
            return {
                'valid': True,
                'original_text': text,
                'sanitized_text': sanitized_text,
                'length': len(sanitized_text)
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Text validation error: {e}")
            raise ValidationError(f"Text validation failed: {e}")
    
    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text by removing dangerous content.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        try:
            if not text:
                return ""
            
            # Remove HTML tags and dangerous content
            sanitized = bleach.clean(
                text,
                tags=[],  # Remove all HTML tags
                attributes={},
                styles=[],
                strip=True
            )
            
            # Remove extra whitespace
            sanitized = ' '.join(sanitized.split())
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Text sanitization error: {e}")
            return text  # Return original if sanitization fails
    
    def _is_safe_filename(self, filename: str) -> bool:
        """
        Check if filename is safe.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if filename is safe
        """
        try:
            # Check for path traversal
            if '..' in filename or '/' in filename or '\\' in filename:
                return False
            
            # Check for dangerous characters
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
            if any(char in filename for char in dangerous_chars):
                return False
            
            # Check filename length
            if len(filename) > 255:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Filename safety check error: {e}")
            return False
    
    def _contains_dangerous_patterns(self, text: str) -> bool:
        """
        Check if text contains dangerous patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if dangerous patterns found
        """
        try:
            for pattern in self.compiled_patterns:
                if pattern.search(text):
                    logger.warning(f"Dangerous pattern detected: {pattern.pattern}")
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Pattern check error: {e}")
            return True  # Assume dangerous if check fails
    
    def validate_url(self, url: str) -> bool:
        """
        Validate URL for security.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is safe
        """
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for localhost/private IPs (basic check)
            hostname = parsed.hostname
            if hostname and (hostname.startswith('127.') or hostname.startswith('192.168.') or 
                           hostname.startswith('10.') or hostname == 'localhost'):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False
    
    def generate_secure_hash(self, data: str) -> str:
        """
        Generate secure hash for data.
        
        Args:
            data: Data to hash
            
        Returns:
            SHA-256 hash of the data
        """
        try:
            return hashlib.sha256(data.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Hash generation error: {e}")
            raise SecurityError(f"Failed to generate hash: {e}")
    
    def validate_json_input(self, json_data: Any) -> Dict[str, Any]:
        """
        Validate JSON input for security.
        
        Args:
            json_data: JSON data to validate
            
        Returns:
            Validation result
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            if not isinstance(json_data, (dict, list)):
                raise ValidationError("JSON data must be an object or array")
            
            # Check depth (prevent deeply nested objects)
            if self._get_json_depth(json_data) > 10:
                raise ValidationError("JSON data is too deeply nested")
            
            # Check size
            json_str = str(json_data)
            if len(json_str) > 1000000:  # 1MB
                raise ValidationError("JSON data is too large")
            
            return {
                'valid': True,
                'depth': self._get_json_depth(json_data),
                'size': len(json_str)
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"JSON validation error: {e}")
            raise ValidationError(f"JSON validation failed: {e}")
    
    def _get_json_depth(self, obj: Any, depth: int = 0) -> int:
        """
        Get the depth of JSON object.
        
        Args:
            obj: JSON object
            depth: Current depth
            
        Returns:
            Maximum depth of the object
        """
        try:
            if isinstance(obj, dict):
                return max((self._get_json_depth(v, depth + 1) for v in obj.values()), default=depth)
            elif isinstance(obj, list):
                return max((self._get_json_depth(item, depth + 1) for item in obj), default=depth)
            else:
                return depth
        except Exception:
            return depth


# Global security validator instance
security_validator = SecurityValidator()
