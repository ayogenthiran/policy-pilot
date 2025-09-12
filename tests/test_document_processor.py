"""
Unit tests for document processing pipeline.
Tests PDF, DOCX, TXT processing, chunking, embedding generation, and indexing.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.services.document_processor import DocumentProcessor
from src.models.document import DocumentStatus, DocumentMetadata, DocumentChunk
from src.utils.exceptions import DocumentProcessingError


class TestDocumentProcessor:
    """Test cases for DocumentProcessor class."""
    
    def test_init(self, document_processor_with_mocks):
        """Test DocumentProcessor initialization."""
        processor = document_processor_with_mocks
        
        assert processor.embedding_service is not None
        assert processor.search_service is not None
        assert processor.file_service is not None
        assert processor.document_loader is not None
        assert processor.text_chunker is not None
    
    def test_process_document_success(self, document_processor_with_mocks, sample_test_files):
        """Test successful document processing."""
        processor = document_processor_with_mocks
        
        # Process a test document
        result = processor.process_document(
            file_path=sample_test_files['txt'],
            filename="test_document.txt"
        )
        
        # Verify result
        assert result.status == DocumentStatus.COMPLETED
        assert result.filename == "test_document.txt"
        assert result.chunks_count > 0
        assert result.processing_time_seconds > 0
        assert result.metadata is not None
        assert len(result.chunks) > 0
        
        # Verify chunks have embeddings
        for chunk in result.chunks:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == 384  # Mock embedding dimension
    
    def test_process_document_file_not_found(self, document_processor_with_mocks):
        """Test document processing with non-existent file."""
        processor = document_processor_with_mocks
        
        with pytest.raises(DocumentProcessingError):
            processor.process_document(
                file_path="/non/existent/file.pdf",
                filename="nonexistent.pdf"
            )
    
    def test_process_document_no_text_content(self, document_processor_with_mocks, test_documents_dir):
        """Test document processing with no text content."""
        processor = document_processor_with_mocks
        
        # Create empty file
        empty_file = test_documents_dir / "empty.txt"
        empty_file.write_text("")
        
        # Mock document loader to return no text content
        processor.document_loader.load_document.return_value = {
            'text_content': [],
            'metadata': {}
        }
        
        result = processor.process_document(
            file_path=str(empty_file),
            filename="empty.txt"
        )
        
        # Should fail processing
        assert result.status == DocumentStatus.FAILED
        assert result.error_message is not None
    
    def test_load_document_success(self, document_processor_with_mocks, sample_test_files):
        """Test document loading functionality."""
        processor = document_processor_with_mocks
        
        # Test loading different file types
        for file_type, file_path in sample_test_files.items():
            result = processor._load_document(file_path, f"test.{file_type}")
            
            assert 'text_content' in result
            assert 'metadata' in result
            assert len(result['text_content']) > 0
    
    def test_load_document_file_not_found(self, document_processor_with_mocks):
        """Test document loading with non-existent file."""
        processor = document_processor_with_mocks
        
        with pytest.raises(DocumentProcessingError):
            processor._load_document("/non/existent/file.pdf", "nonexistent.pdf")
    
    def test_create_document_metadata(self, document_processor_with_mocks, sample_test_files):
        """Test document metadata creation."""
        processor = document_processor_with_mocks
        
        # Mock document data
        document_data = {
            'text_content': ["Test content"],
            'metadata': {
                'title': 'Test Document',
                'author': 'Test Author',
                'total_pages': 5,
                'language': 'en'
            }
        }
        
        metadata = processor._create_document_metadata(
            document_data, "test.pdf", sample_test_files['pdf']
        )
        
        assert metadata.title == 'Test Document'
        assert metadata.author == 'Test Author'
        assert metadata.file_size > 0
        assert metadata.file_type == 'application/pdf'
        assert metadata.total_pages == 5
        assert metadata.language == 'en'
    
    def test_chunk_document(self, document_processor_with_mocks):
        """Test document chunking functionality."""
        processor = document_processor_with_mocks
        
        # Mock document data
        document_data = {
            'text_content': [
                "This is the first paragraph with some content.",
                "This is the second paragraph with different content.",
                "This is the third paragraph with more content."
            ],
            'metadata': {}
        }
        
        chunks = processor._chunk_document(
            document_data, "test_doc", DocumentMetadata(
                title="Test Doc",
                file_size=1000,
                file_type="text/plain"
            )
        )
        
        assert len(chunks) == 3
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_id == f"test_doc_chunk_{i}"
            assert chunk.content == document_data['text_content'][i]
            assert chunk.chunk_index == i
            assert chunk.page_number == i + 1
            assert chunk.word_count > 0
            assert chunk.char_count > 0
    
    def test_generate_embeddings(self, document_processor_with_mocks, sample_document_chunks):
        """Test embedding generation for chunks."""
        processor = document_processor_with_mocks
        
        # Generate embeddings
        chunks_with_embeddings = processor._generate_embeddings(sample_document_chunks)
        
        assert len(chunks_with_embeddings) == len(sample_document_chunks)
        
        for chunk in chunks_with_embeddings:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == 384  # Mock embedding dimension
            assert isinstance(chunk.embedding, list)
            assert all(isinstance(x, float) for x in chunk.embedding)
    
    def test_generate_embeddings_empty_chunks(self, document_processor_with_mocks):
        """Test embedding generation with empty chunks list."""
        processor = document_processor_with_mocks
        
        result = processor._generate_embeddings([])
        assert result == []
    
    def test_index_documents(self, document_processor_with_mocks, sample_document_chunks):
        """Test document indexing functionality."""
        processor = document_processor_with_mocks
        
        # Add embeddings to chunks
        for chunk in sample_document_chunks:
            chunk.embedding = [0.1] * 384
        
        result = processor._index_documents(sample_document_chunks, "test_doc")
        
        assert result['success'] is True
        assert result['indexed_count'] == 5  # Mock value
        assert result['failed_count'] == 0
        
        # Verify search service was called
        processor.search_service.index_documents.assert_called_once()
    
    def test_index_documents_empty_chunks(self, document_processor_with_mocks):
        """Test indexing with empty chunks list."""
        processor = document_processor_with_mocks
        
        result = processor._index_documents([], "test_doc")
        
        assert result['success'] is True
        assert result['indexed_count'] == 0
        assert result['failed_count'] == 0
    
    def test_get_file_type(self, document_processor_with_mocks):
        """Test file type detection."""
        processor = document_processor_with_mocks
        
        # Test different file extensions
        test_cases = [
            ("document.pdf", "application/pdf"),
            ("document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("document.doc", "application/msword"),
            ("document.txt", "text/plain"),
            ("document.md", "text/markdown"),
            ("document.rtf", "application/rtf"),
            ("document.unknown", "application/octet-stream")
        ]
        
        for filename, expected_type in test_cases:
            result = processor._get_file_type(filename)
            assert result == expected_type
    
    def test_get_processing_stats(self, document_processor_with_mocks):
        """Test processing statistics retrieval."""
        processor = document_processor_with_mocks
        
        stats = processor.get_processing_stats()
        
        assert 'embedding_service' in stats
        assert 'search_service' in stats
        assert 'document_stats' in stats
        assert 'chunk_size' in stats
        assert 'chunk_overlap' in stats
        
        assert stats['embedding_service']['status'] == 'healthy'
        assert stats['search_service']['status'] == 'healthy'
        assert stats['chunk_size'] == 1000
        assert stats['chunk_overlap'] == 200
    
    def test_health_check_healthy(self, document_processor_with_mocks):
        """Test health check when all services are healthy."""
        processor = document_processor_with_mocks
        
        health = processor.health_check()
        
        assert health['status'] == 'healthy'
        assert 'embedding_service' in health
        assert 'search_service' in health
        assert 'services_available' in health
        assert health['services_available']['embedding'] is True
        assert health['services_available']['search'] is True
    
    def test_health_check_degraded(self, document_processor_with_mocks):
        """Test health check when one service is degraded."""
        processor = document_processor_with_mocks
        
        # Mock one service as degraded
        processor.embedding_service.health_check.return_value = {
            'status': 'degraded'
        }
        
        health = processor.health_check()
        
        assert health['status'] == 'degraded'
    
    def test_health_check_unhealthy(self, document_processor_with_mocks):
        """Test health check when services are unhealthy."""
        processor = document_processor_with_mocks
        
        # Mock services as unhealthy
        processor.embedding_service.health_check.return_value = {
            'status': 'unhealthy'
        }
        processor.search_service.health_check.return_value = {
            'status': 'unhealthy'
        }
        
        health = processor.health_check()
        
        assert health['status'] == 'unhealthy'
    
    def test_health_check_exception(self, document_processor_with_mocks):
        """Test health check when an exception occurs."""
        processor = document_processor_with_mocks
        
        # Mock service to raise exception
        processor.embedding_service.health_check.side_effect = Exception("Service error")
        
        health = processor.health_check()
        
        assert health['status'] == 'unhealthy'
        assert 'error' in health
    
    def test_process_document_with_different_file_types(self, document_processor_with_mocks, sample_test_files):
        """Test processing different file types."""
        processor = document_processor_with_mocks
        
        # Test PDF processing
        pdf_result = processor.process_document(
            file_path=sample_test_files['pdf'],
            filename="test.pdf"
        )
        assert pdf_result.status == DocumentStatus.COMPLETED
        assert pdf_result.metadata.file_type == "application/pdf"
        
        # Test TXT processing
        txt_result = processor.process_document(
            file_path=sample_test_files['txt'],
            filename="test.txt"
        )
        assert txt_result.status == DocumentStatus.COMPLETED
        assert txt_result.metadata.file_type == "text/plain"
    
    def test_process_document_large_file(self, document_processor_with_mocks, sample_test_files):
        """Test processing large files for chunking."""
        processor = document_processor_with_mocks
        
        # Process large text file
        result = processor.process_document(
            file_path=sample_test_files['large_txt'],
            filename="large_test_document.txt"
        )
        
        assert result.status == DocumentStatus.COMPLETED
        assert result.chunks_count > 0
        assert len(result.chunks) > 0
        
        # Verify chunks are properly created
        for chunk in result.chunks:
            assert chunk.content is not None
            assert len(chunk.content) > 0
            assert chunk.embedding is not None
    
    def test_process_document_error_handling(self, document_processor_with_mocks):
        """Test error handling during document processing."""
        processor = document_processor_with_mocks
        
        # Mock document loader to raise exception
        processor.document_loader.load_document.side_effect = Exception("Load error")
        
        result = processor.process_document(
            file_path="/fake/path.pdf",
            filename="fake.pdf"
        )
        
        assert result.status == DocumentStatus.FAILED
        assert result.error_message is not None
        assert "Load error" in result.error_message
    
    def test_chunk_metadata_validation(self, document_processor_with_mocks):
        """Test that chunk metadata is properly validated."""
        processor = document_processor_with_mocks
        
        # Mock document data
        document_data = {
            'text_content': ["Test content"],
            'metadata': {}
        }
        
        chunks = processor._chunk_document(
            document_data, "test_doc", DocumentMetadata(
                title="Test Doc",
                file_size=1000,
                file_type="text/plain"
            )
        )
        
        assert len(chunks) == 1
        chunk = chunks[0]
        
        # Verify metadata structure
        assert 'chunk_index' in chunk.metadata
        assert 'document_id' in chunk.metadata
        assert 'page_number' in chunk.metadata
        assert chunk.metadata['document_id'] == "test_doc"
        assert chunk.metadata['chunk_index'] == 0
        assert chunk.metadata['page_number'] == 1
    
    def test_embedding_consistency(self, document_processor_with_mocks, sample_document_chunks):
        """Test that embeddings are consistent for the same text."""
        processor = document_processor_with_mocks
        
        # Generate embeddings twice for the same chunks
        chunks1 = processor._generate_embeddings(sample_document_chunks)
        chunks2 = processor._generate_embeddings(sample_document_chunks)
        
        # Embeddings should be identical (due to seeded random)
        for chunk1, chunk2 in zip(chunks1, chunks2):
            assert chunk1.embedding == chunk2.embedding
    
    def test_processing_time_calculation(self, document_processor_with_mocks, sample_test_files):
        """Test that processing time is calculated correctly."""
        processor = document_processor_with_mocks
        
        result = processor.process_document(
            file_path=sample_test_files['txt'],
            filename="test.txt"
        )
        
        assert result.processing_time_seconds is not None
        assert result.processing_time_seconds > 0
        assert result.created_at is not None
        assert result.completed_at is not None
        assert result.completed_at >= result.created_at
