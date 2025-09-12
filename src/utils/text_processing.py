"""
Text processing utilities for Policy Pilot RAG backend.
Handles intelligent text chunking and content processing.
"""

import re
from typing import Dict, List, Any, Optional, Union
from uuid import uuid4

from src.config.settings import settings
from src.core.logging import get_logger
from src.utils.exceptions import DocumentProcessingError, ValidationError

logger = get_logger(__name__)


class TextChunker:
    """Class for intelligent text chunking with configurable size and overlap."""
    
    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Size of each chunk in characters (default from settings)
            chunk_overlap: Overlap between chunks in characters (default from settings)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        # Validate parameters
        if self.chunk_size <= 0:
            raise ValidationError("Chunk size must be positive")
        if self.chunk_overlap < 0:
            raise ValidationError("Chunk overlap must be non-negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValidationError("Chunk overlap must be less than chunk size")
        
        # Sentence boundary patterns
        self.sentence_endings = re.compile(r'[.!?]+\s+')
        self.paragraph_endings = re.compile(r'\n\s*\n')
        
        logger.info(f"TextChunker initialized: chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")
    
    def chunk_document(self, document_data: Dict[str, Any], document_id: str) -> List[Dict[str, Any]]:
        """
        Chunk a document into overlapping chunks.
        
        Args:
            document_data: Document data from DocumentLoader
            document_id: Unique document identifier
            
        Returns:
            List of chunk dictionaries
            
        Raises:
            DocumentProcessingError: If chunking fails
        """
        try:
            text_content = document_data.get('text_content', [])
            metadata = document_data.get('metadata', {})
            
            if not text_content:
                raise DocumentProcessingError("No text content to chunk")
            
            # Combine content based on file type
            combined_content = self._combine_content(text_content, metadata.get('file_type', ''))
            
            if not combined_content.strip():
                raise DocumentProcessingError("No content to chunk after combining")
            
            # Create chunks
            chunks = self._create_chunks(combined_content, document_id, metadata)
            
            logger.info(f"Document chunked: {len(chunks)} chunks created for {document_id}")
            return chunks
            
        except DocumentProcessingError:
            raise
        except Exception as e:
            logger.error(f"Failed to chunk document {document_id}: {e}")
            raise DocumentProcessingError(f"Failed to chunk document: {e}")
    
    def _combine_content(self, text_content: List[Dict[str, Any]], file_type: str) -> str:
        """
        Combine text content based on file type.
        
        Args:
            text_content: List of text elements from document
            file_type: Type of file being processed
            
        Returns:
            Combined text content
        """
        try:
            combined_parts = []
            
            if file_type == 'pdf':
                # For PDF, combine by pages
                for element in text_content:
                    if 'page_number' in element:
                        page_text = element['content']
                        if page_text.strip():
                            combined_parts.append(f"Page {element['page_number']}:\n{page_text}")
            
            elif file_type in ['docx', 'doc']:
                # For DOCX, combine paragraphs and tables
                for element in text_content:
                    content = element['content']
                    if content.strip():
                        if 'style' in element and 'Heading' in element['style']:
                            # Add extra spacing for headings
                            combined_parts.append(f"\n{content}\n")
                        else:
                            combined_parts.append(content)
            
            else:
                # For text files, combine paragraphs
                for element in text_content:
                    content = element['content']
                    if content.strip():
                        combined_parts.append(content)
            
            # Join with appropriate separators
            if file_type == 'pdf':
                separator = '\n\n'
            else:
                separator = '\n\n'
            
            combined_text = separator.join(combined_parts)
            
            # Clean up whitespace
            combined_text = re.sub(r'\n\s*\n\s*\n', '\n\n', combined_text)
            combined_text = combined_text.strip()
            
            logger.debug(f"Content combined: {len(combined_text)} characters")
            return combined_text
            
        except Exception as e:
            logger.error(f"Failed to combine content: {e}")
            raise DocumentProcessingError(f"Failed to combine document content: {e}")
    
    def _create_chunks(self, text: str, document_id: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create chunks from text with intelligent boundary detection.
        
        Args:
            text: Text to chunk
            document_id: Document identifier
            metadata: Document metadata
            
        Returns:
            List of chunk dictionaries
        """
        try:
            chunks = []
            text_length = len(text)
            
            if text_length <= self.chunk_size:
                # Single chunk if text is small enough
                chunk = self._create_single_chunk(text, document_id, 0, metadata)
                chunks.append(chunk)
                return chunks
            
            # Split into chunks with overlap
            start = 0
            chunk_index = 0
            
            while start < text_length:
                # Calculate end position
                end = min(start + self.chunk_size, text_length)
                
                # Extract chunk text
                chunk_text = text[start:end]
                
                # Try to break at sentence boundary
                if end < text_length:
                    chunk_text = self._break_at_sentence_boundary(chunk_text, text, start, end)
                
                # Create chunk
                chunk = self._create_single_chunk(
                    chunk_text, document_id, chunk_index, metadata, start, end
                )
                chunks.append(chunk)
                
                # Move start position (with overlap)
                start = end - self.chunk_overlap
                chunk_index += 1
                
                # Prevent infinite loop
                if start >= text_length - self.chunk_overlap:
                    break
            
            # Ensure we don't miss the end of the text
            if start < text_length:
                remaining_text = text[start:]
                if len(remaining_text.strip()) > 0:
                    chunk = self._create_single_chunk(
                        remaining_text, document_id, chunk_index, metadata, start, text_length
                    )
                    chunks.append(chunk)
            
            logger.debug(f"Created {len(chunks)} chunks from {text_length} characters")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to create chunks: {e}")
            raise DocumentProcessingError(f"Failed to create text chunks: {e}")
    
    def _break_at_sentence_boundary(self, chunk_text: str, full_text: str, start: int, end: int) -> str:
        """
        Break chunk at sentence boundary if possible.
        
        Args:
            chunk_text: Current chunk text
            full_text: Full document text
            start: Start position in full text
            end: End position in full text
            
        Returns:
            Adjusted chunk text
        """
        try:
            # Look for sentence endings in the last 20% of the chunk
            search_start = max(0, int(len(chunk_text) * 0.8))
            search_text = chunk_text[search_start:]
            
            # Find last sentence ending
            matches = list(self.sentence_endings.finditer(search_text))
            if matches:
                last_match = matches[-1]
                # Adjust end position
                new_end = start + search_start + last_match.end()
                return full_text[start:new_end]
            
            return chunk_text
            
        except Exception as e:
            logger.warning(f"Failed to break at sentence boundary: {e}")
            return chunk_text
    
    def _create_single_chunk(self, text: str, document_id: str, chunk_index: int, 
                           metadata: Dict[str, Any], start_pos: Optional[int] = None, 
                           end_pos: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a single chunk dictionary.
        
        Args:
            text: Chunk text content
            document_id: Document identifier
            chunk_index: Index of chunk in document
            metadata: Document metadata
            start_pos: Start position in original text
            end_pos: End position in original text
            
        Returns:
            Chunk dictionary
        """
        try:
            # Generate unique chunk ID
            chunk_id = f"{document_id}_chunk_{chunk_index}_{uuid4().hex[:8]}"
            
            # Calculate statistics
            word_count = len(text.split())
            char_count = len(text)
            
            # Extract page number if available (for PDF)
            page_number = None
            if 'file_type' in metadata and metadata['file_type'] == 'pdf':
                page_match = re.search(r'Page (\d+):', text)
                if page_match:
                    page_number = int(page_match.group(1))
            
            # Create chunk metadata
            chunk_metadata = {
                'chunk_index': chunk_index,
                'start_position': start_pos,
                'end_position': end_pos,
                'word_count': word_count,
                'char_count': char_count,
                'file_type': metadata.get('file_type', ''),
                'extraction_method': metadata.get('extraction_method', ''),
                'page_number': page_number
            }
            
            # Add document-level metadata
            chunk_metadata.update({
                'document_title': metadata.get('title', ''),
                'document_author': metadata.get('author', ''),
                'document_created': metadata.get('created', ''),
                'document_modified': metadata.get('modified', '')
            })
            
            chunk = {
                'chunk_id': chunk_id,
                'content': text.strip(),
                'metadata': chunk_metadata,
                'word_count': word_count,
                'char_count': char_count,
                'page_number': page_number
            }
            
            return chunk
            
        except Exception as e:
            logger.error(f"Failed to create chunk {chunk_index}: {e}")
            raise DocumentProcessingError(f"Failed to create chunk: {e}")
    
    def get_chunk_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Statistics dictionary
        """
        try:
            if not chunks:
                return {
                    'total_chunks': 0,
                    'total_words': 0,
                    'total_characters': 0,
                    'average_words_per_chunk': 0,
                    'average_characters_per_chunk': 0,
                    'min_words': 0,
                    'max_words': 0,
                    'min_characters': 0,
                    'max_characters': 0
                }
            
            word_counts = [chunk['word_count'] for chunk in chunks]
            char_counts = [chunk['char_count'] for chunk in chunks]
            
            stats = {
                'total_chunks': len(chunks),
                'total_words': sum(word_counts),
                'total_characters': sum(char_counts),
                'average_words_per_chunk': round(sum(word_counts) / len(chunks), 2),
                'average_characters_per_chunk': round(sum(char_counts) / len(chunks), 2),
                'min_words': min(word_counts),
                'max_words': max(word_counts),
                'min_characters': min(char_counts),
                'max_characters': max(char_counts)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to calculate chunk statistics: {e}")
            return {'error': str(e)}
    
    def validate_chunks(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Validate chunks and return any issues found.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of validation issues
        """
        issues = []
        
        try:
            for i, chunk in enumerate(chunks):
                # Check required fields
                required_fields = ['chunk_id', 'content', 'metadata']
                for field in required_fields:
                    if field not in chunk:
                        issues.append(f"Chunk {i}: Missing required field '{field}'")
                
                # Check content
                if 'content' in chunk and not chunk['content'].strip():
                    issues.append(f"Chunk {i}: Empty content")
                
                # Check word count consistency
                if 'content' in chunk and 'word_count' in chunk:
                    actual_words = len(chunk['content'].split())
                    if actual_words != chunk['word_count']:
                        issues.append(f"Chunk {i}: Word count mismatch")
                
                # Check character count consistency
                if 'content' in chunk and 'char_count' in chunk:
                    actual_chars = len(chunk['content'])
                    if actual_chars != chunk['char_count']:
                        issues.append(f"Chunk {i}: Character count mismatch")
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to validate chunks: {e}")
            return [f"Validation error: {e}"]
