"""
File handling service for Policy Pilot RAG backend.
Manages file uploads, validation, and storage operations.
"""

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from uuid import uuid4

from src.config.settings import settings
from src.core.logging import get_logger
from src.utils.exceptions import FileUploadError, ValidationError, PolicyPilotException

logger = get_logger(__name__)


class FileService:
    """Service for handling file operations."""
    
    # Supported file types and their MIME types
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.rtf': 'application/rtf'
    }
    
    def __init__(self):
        """Initialize the file service."""
        self.upload_dir = Path(settings.upload_dir)
        self.data_dir = Path(settings.data_dir)
        self.max_file_size = settings.max_file_size
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure upload and data directories exist."""
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directories: {self.upload_dir}, {self.data_dir}")
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            raise PolicyPilotException(f"Failed to create required directories: {e}")
    
    def validate_file(self, filename: str, file_size: int, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate uploaded file.
        
        Args:
            filename: Name of the file
            file_size: Size of the file in bytes
            content_type: MIME type of the file
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ValidationError: If file validation fails
        """
        try:
            # Check file size
            if file_size > self.max_file_size:
                raise ValidationError(
                    f"File size {file_size} exceeds maximum allowed size {self.max_file_size} bytes"
                )
            
            if file_size == 0:
                raise ValidationError("File is empty")
            
            # Get file extension
            file_path = Path(filename)
            extension = file_path.suffix.lower()
            
            if extension not in self.SUPPORTED_EXTENSIONS:
                raise ValidationError(
                    f"Unsupported file type: {extension}. "
                    f"Supported types: {', '.join(self.SUPPORTED_EXTENSIONS.keys())}"
                )
            
            # Validate MIME type if provided
            if content_type:
                expected_mime = self.SUPPORTED_EXTENSIONS[extension]
                if content_type != expected_mime:
                    logger.warning(
                        f"MIME type mismatch: expected {expected_mime}, got {content_type}"
                    )
            
            # Get MIME type
            mime_type = self.SUPPORTED_EXTENSIONS[extension]
            
            validation_result = {
                'valid': True,
                'extension': extension,
                'mime_type': mime_type,
                'file_size': file_size,
                'filename': filename
            }
            
            logger.info(f"File validation successful: {filename}")
            return validation_result
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"File validation error: {e}")
            raise ValidationError(f"File validation failed: {e}")
    
    def save_uploaded_file(self, file_content: bytes, filename: str, 
                          document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Save uploaded file to the uploads directory.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            document_id: Optional document ID (generated if not provided)
            
        Returns:
            Dictionary with file information
            
        Raises:
            FileUploadError: If file saving fails
        """
        try:
            # Generate document ID if not provided
            if not document_id:
                document_id = self.generate_document_id(file_content, filename)
            
            # Create document directory
            doc_dir = self.upload_dir / document_id
            doc_dir.mkdir(exist_ok=True)
            
            # Save file
            file_path = doc_dir / filename
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Get file info
            file_info = {
                'document_id': document_id,
                'filename': filename,
                'file_path': str(file_path),
                'file_size': len(file_content),
                'uploaded_at': datetime.utcnow(),
                'directory': str(doc_dir)
            }
            
            logger.info(f"File saved successfully: {filename} -> {file_path}")
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {e}")
            raise FileUploadError(f"Failed to save uploaded file: {e}")
    
    def generate_document_id(self, file_content: bytes, filename: str) -> str:
        """
        Generate unique document ID based on file content and metadata.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Unique document ID
        """
        try:
            # Create hash from content and filename
            content_hash = hashlib.sha256(file_content).hexdigest()[:16]
            filename_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
            timestamp = str(int(datetime.utcnow().timestamp()))[-6:]
            
            # Combine to create unique ID
            document_id = f"doc_{content_hash}_{filename_hash}_{timestamp}"
            
            logger.debug(f"Generated document ID: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to generate document ID: {e}")
            # Fallback to UUID
            return f"doc_{uuid4().hex[:16]}"
    
    def get_file_path(self, document_id: str, filename: str) -> Path:
        """
        Get file path for a document.
        
        Args:
            document_id: Document ID
            filename: Filename
            
        Returns:
            Path to the file
        """
        return self.upload_dir / document_id / filename
    
    def file_exists(self, document_id: str, filename: str) -> bool:
        """
        Check if file exists.
        
        Args:
            document_id: Document ID
            filename: Filename
            
        Returns:
            True if file exists, False otherwise
        """
        file_path = self.get_file_path(document_id, filename)
        return file_path.exists()
    
    def get_file_info(self, document_id: str, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get file information.
        
        Args:
            document_id: Document ID
            filename: Filename
            
        Returns:
            File information dictionary or None if file doesn't exist
        """
        try:
            file_path = self.get_file_path(document_id, filename)
            
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            return {
                'document_id': document_id,
                'filename': filename,
                'file_path': str(file_path),
                'file_size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime)
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info for {document_id}/{filename}: {e}")
            return None
    
    def cleanup_temp_file(self, file_path: str) -> bool:
        """
        Remove temporary file.
        
        Args:
            file_path: Path to the file to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.debug(f"Cleaned up temporary file: {file_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to cleanup file {file_path}: {e}")
            return False
    
    def cleanup_document_directory(self, document_id: str) -> bool:
        """
        Remove entire document directory.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_dir = self.upload_dir / document_id
            if doc_dir.exists():
                shutil.rmtree(doc_dir)
                logger.info(f"Cleaned up document directory: {doc_dir}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to cleanup document directory {document_id}: {e}")
            return False
    
    def list_document_files(self, document_id: str) -> List[Dict[str, Any]]:
        """
        List files in a document directory.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of file information dictionaries
        """
        try:
            doc_dir = self.upload_dir / document_id
            if not doc_dir.exists():
                return []
            
            files = []
            for file_path in doc_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        'filename': file_path.name,
                        'file_size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_ctime),
                        'modified_at': datetime.fromtimestamp(stat.st_mtime)
                    })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files for document {document_id}: {e}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            total_files = 0
            total_size = 0
            document_count = 0
            
            for doc_dir in self.upload_dir.iterdir():
                if doc_dir.is_dir():
                    document_count += 1
                    for file_path in doc_dir.iterdir():
                        if file_path.is_file():
                            total_files += 1
                            total_size += file_path.stat().st_size
            
            return {
                'total_documents': document_count,
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'upload_directory': str(self.upload_dir),
                'max_file_size': self.max_file_size
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                'total_documents': 0,
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'upload_directory': str(self.upload_dir),
                'max_file_size': self.max_file_size
            }
