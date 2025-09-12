"""
Integration tests for complete RAG pipeline.
Tests document upload, processing, query processing, and error handling.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.services.rag_service import RAGService
from src.models.document import DocumentStatus, DocumentMetadata, DocumentChunk
from src.models.query import QueryRequest, QueryResponse, SearchType, Source
from src.utils.exceptions import DocumentProcessingError, SearchServiceError, GPTServiceError


class TestRAGService:
    """Test cases for RAGService class."""
    
    def test_init(self, rag_service_with_mocks):
        """Test RAGService initialization."""
        rag_service = rag_service_with_mocks
        
        assert rag_service.document_processor is not None
        assert rag_service.embedding_service is not None
        assert rag_service.search_service is not None
        assert rag_service.gpt_service is not None
    
    def test_process_document_success(self, rag_service_with_mocks, sample_test_files):
        """Test successful document processing through RAG service."""
        rag_service = rag_service_with_mocks
        
        # Mock document processor to return successful result
        mock_processed_doc = Mock()
        mock_processed_doc.status = DocumentStatus.COMPLETED
        mock_processed_doc.document_id = "test_doc_123"
        mock_processed_doc.filename = "test.pdf"
        mock_processed_doc.chunks_count = 5
        mock_processed_doc.processing_time_seconds = 2.5
        mock_processed_doc.error_message = None
        
        rag_service.document_processor.process_document.return_value = mock_processed_doc
        
        result = rag_service.process_document(
            file_path=sample_test_files['pdf'],
            filename="test.pdf"
        )
        
        assert result.status == DocumentStatus.COMPLETED
        assert result.document_id == "test_doc_123"
        assert result.filename == "test.pdf"
        assert result.chunks_count == 5
        assert result.processing_time_seconds == 2.5
        
        # Verify document processor was called
        rag_service.document_processor.process_document.assert_called_once()
    
    def test_process_document_failure(self, rag_service_with_mocks, sample_test_files):
        """Test document processing failure handling."""
        rag_service = rag_service_with_mocks
        
        # Mock document processor to raise exception
        rag_service.document_processor.process_document.side_effect = DocumentProcessingError("Processing failed")
        
        with pytest.raises(DocumentProcessingError):
            rag_service.process_document(
                file_path=sample_test_files['pdf'],
                filename="test.pdf"
            )
    
    def test_query_documents_with_rag(self, rag_service_with_mocks, sample_query_request):
        """Test query processing with RAG enabled."""
        rag_service = rag_service_with_mocks
        
        # Mock embedding generation
        mock_embedding = np.random.rand(384).astype(np.float32)
        rag_service.embedding_service.get_embedding.return_value = mock_embedding
        
        # Mock search results
        mock_sources = [
            Source(
                content="Test content 1",
                document_name="Test Doc 1",
                score=0.9,
                chunk_id="chunk_1",
                page_number=1,
                metadata={"chunk_index": 0},
                document_id="doc_1",
                document_title="Test Document 1"
            ),
            Source(
                content="Test content 2",
                document_name="Test Doc 2",
                score=0.8,
                chunk_id="chunk_2",
                page_number=2,
                metadata={"chunk_index": 1},
                document_id="doc_2",
                document_title="Test Document 2"
            )
        ]
        
        # Mock search service
        rag_service.search_service.hybrid_search.return_value = mock_sources
        
        # Mock GPT service
        mock_response = QueryResponse(
            question=sample_query_request.question,
            answer="Test answer based on retrieved sources",
            sources=mock_sources,
            search_type=sample_query_request.search_type,
            total_sources=len(mock_sources),
            tokens_used=150,
            processing_time=1.0
        )
        rag_service.gpt_service.generate_answer.return_value = mock_response
        
        # Execute query
        result = rag_service.query_documents(sample_query_request)
        
        # Verify result
        assert result.question == sample_query_request.question
        assert result.answer == "Test answer based on retrieved sources"
        assert len(result.sources) == 2
        assert result.total_sources == 2
        assert result.tokens_used == 150
        assert result.processing_time > 0
        
        # Verify services were called
        rag_service.embedding_service.get_embedding.assert_called_once()
        rag_service.search_service.hybrid_search.assert_called_once()
        rag_service.gpt_service.generate_answer.assert_called_once()
    
    def test_query_documents_without_rag(self, rag_service_with_mocks):
        """Test query processing with RAG disabled."""
        rag_service = rag_service_with_mocks
        
        # Create query without RAG
        query_request = QueryRequest(
            question="What is the weather like?",
            use_rag=False,
            search_type=SearchType.SEMANTIC,
            top_k=5
        )
        
        # Mock GPT service
        mock_response = QueryResponse(
            question=query_request.question,
            answer="I cannot answer that question without access to documents.",
            sources=[],
            search_type=query_request.search_type,
            total_sources=0,
            tokens_used=50,
            processing_time=0.5
        )
        rag_service.gpt_service.generate_answer.return_value = mock_response
        
        # Execute query
        result = rag_service.query_documents(query_request)
        
        # Verify result
        assert result.question == query_request.question
        assert len(result.sources) == 0
        assert result.total_sources == 0
        
        # Verify embedding and search services were not called
        rag_service.embedding_service.get_embedding.assert_not_called()
        rag_service.search_service.hybrid_search.assert_not_called()
        
        # Verify GPT service was called
        rag_service.gpt_service.generate_answer.assert_called_once()
    
    def test_query_documents_embedding_failure(self, rag_service_with_mocks, sample_query_request):
        """Test query processing when embedding generation fails."""
        rag_service = rag_service_with_mocks
        
        # Mock embedding service to return None
        rag_service.embedding_service.get_embedding.return_value = None
        
        # Mock GPT service
        mock_response = QueryResponse(
            question=sample_query_request.question,
            answer="I encountered an error while processing your query.",
            sources=[],
            search_type=sample_query_request.search_type,
            total_sources=0,
            tokens_used=0,
            processing_time=0.1
        )
        rag_service.gpt_service.generate_answer.return_value = mock_response
        
        # Execute query
        result = rag_service.query_documents(sample_query_request)
        
        # Verify result
        assert result.question == sample_query_request.question
        assert len(result.sources) == 0
        assert result.total_sources == 0
        
        # Verify search service was not called
        rag_service.search_service.hybrid_search.assert_not_called()
    
    def test_query_documents_search_failure(self, rag_service_with_mocks, sample_query_request):
        """Test query processing when search fails."""
        rag_service = rag_service_with_mocks
        
        # Mock embedding generation
        mock_embedding = np.random.rand(384).astype(np.float32)
        rag_service.embedding_service.get_embedding.return_value = mock_embedding
        
        # Mock search service to return empty results
        rag_service.search_service.hybrid_search.return_value = []
        
        # Mock GPT service
        mock_response = QueryResponse(
            question=sample_query_request.question,
            answer="I couldn't find relevant information to answer your question.",
            sources=[],
            search_type=sample_query_request.search_type,
            total_sources=0,
            tokens_used=100,
            processing_time=0.8
        )
        rag_service.gpt_service.generate_answer.return_value = mock_response
        
        # Execute query
        result = rag_service.query_documents(sample_query_request)
        
        # Verify result
        assert result.question == sample_query_request.question
        assert len(result.sources) == 0
        assert result.total_sources == 0
    
    def test_query_documents_gpt_failure(self, rag_service_with_mocks, sample_query_request):
        """Test query processing when GPT service fails."""
        rag_service = rag_service_with_mocks
        
        # Mock embedding generation
        mock_embedding = np.random.rand(384).astype(np.float32)
        rag_service.embedding_service.get_embedding.return_value = mock_embedding
        
        # Mock search results
        mock_sources = [Source(
            content="Test content",
            document_name="Test Doc",
            score=0.9,
            chunk_id="chunk_1",
            page_number=1,
            metadata={"chunk_index": 0},
            document_id="doc_1",
            document_title="Test Document"
        )]
        rag_service.search_service.hybrid_search.return_value = mock_sources
        
        # Mock GPT service to raise exception
        rag_service.gpt_service.generate_answer.side_effect = GPTServiceError("GPT service error")
        
        # Execute query
        result = rag_service.query_documents(sample_query_request)
        
        # Verify error response
        assert result.question == sample_query_request.question
        assert "error" in result.answer.lower()
        assert result.error is not None
        assert "GPT service error" in result.error
    
    def test_generate_query_embedding_success(self, rag_service_with_mocks):
        """Test successful query embedding generation."""
        rag_service = rag_service_with_mocks
        
        # Mock embedding generation
        mock_embedding = np.random.rand(384).astype(np.float32)
        rag_service.embedding_service.get_embedding.return_value = mock_embedding
        
        result = rag_service._generate_query_embedding("Test question")
        
        assert result is not None
        assert len(result) == 384
        assert all(isinstance(x, float) for x in result)
    
    def test_generate_query_embedding_failure(self, rag_service_with_mocks):
        """Test query embedding generation failure."""
        rag_service = rag_service_with_mocks
        
        # Mock embedding service to raise exception
        rag_service.embedding_service.get_embedding.side_effect = Exception("Embedding error")
        
        result = rag_service._generate_query_embedding("Test question")
        
        assert result is None
    
    def test_search_documents_success(self, rag_service_with_mocks, sample_query_request):
        """Test successful document search."""
        rag_service = rag_service_with_mocks
        
        # Mock search results
        mock_search_results = [
            Mock(
                content="Test content 1",
                document_title="Test Doc 1",
                score=0.9,
                chunk_id="chunk_1",
                page_number=1,
                metadata={"chunk_index": 0},
                document_id="doc_1",
                document_filename="test1.pdf"
            ),
            Mock(
                content="Test content 2",
                document_title="Test Doc 2",
                score=0.8,
                chunk_id="chunk_2",
                page_number=2,
                metadata={"chunk_index": 1},
                document_id="doc_2",
                document_filename="test2.pdf"
            )
        ]
        rag_service.search_service.hybrid_search.return_value = mock_search_results
        
        query_embedding = [0.1] * 384
        result = rag_service._search_documents(sample_query_request, query_embedding)
        
        assert len(result) == 2
        assert all(isinstance(source, Source) for source in result)
        assert result[0].content == "Test content 1"
        assert result[0].score == 0.9
        assert result[1].content == "Test content 2"
        assert result[1].score == 0.8
    
    def test_search_documents_failure(self, rag_service_with_mocks, sample_query_request):
        """Test document search failure."""
        rag_service = rag_service_with_mocks
        
        # Mock search service to raise exception
        rag_service.search_service.hybrid_search.side_effect = SearchServiceError("Search error")
        
        query_embedding = [0.1] * 384
        result = rag_service._search_documents(sample_query_request, query_embedding)
        
        assert result == []
    
    def test_generate_answer_success(self, rag_service_with_mocks, sample_query_request):
        """Test successful answer generation."""
        rag_service = rag_service_with_mocks
        
        # Mock sources
        mock_sources = [Source(
            content="Test content",
            document_name="Test Doc",
            score=0.9,
            chunk_id="chunk_1",
            page_number=1,
            metadata={"chunk_index": 0},
            document_id="doc_1",
            document_title="Test Document"
        )]
        
        # Mock GPT service
        mock_response = QueryResponse(
            question=sample_query_request.question,
            answer="Test answer",
            sources=mock_sources,
            search_type=sample_query_request.search_type,
            total_sources=1,
            tokens_used=100,
            processing_time=0.5
        )
        rag_service.gpt_service.generate_answer.return_value = mock_response
        
        result = rag_service._generate_answer(sample_query_request, mock_sources)
        
        assert result.question == sample_query_request.question
        assert result.answer == "Test answer"
        assert len(result.sources) == 1
        assert result.total_sources == 1
        assert result.tokens_used == 100
    
    def test_generate_answer_failure(self, rag_service_with_mocks, sample_query_request):
        """Test answer generation failure."""
        rag_service = rag_service_with_mocks
        
        # Mock GPT service to raise exception
        rag_service.gpt_service.generate_answer.side_effect = GPTServiceError("GPT error")
        
        mock_sources = []
        
        with pytest.raises(GPTServiceError):
            rag_service._generate_answer(sample_query_request, mock_sources)
    
    def test_get_system_health_healthy(self, rag_service_with_mocks):
        """Test system health check when all services are healthy."""
        rag_service = rag_service_with_mocks
        
        health = rag_service.get_system_health()
        
        assert health['status'] == 'healthy'
        assert 'timestamp' in health
        assert 'services' in health
        assert 'statistics' in health
        assert 'configuration' in health
        
        # Check individual services
        assert health['services']['embedding_service']['status'] == 'healthy'
        assert health['services']['search_service']['status'] == 'healthy'
        assert health['services']['gpt_service']['status'] == 'healthy'
        assert health['services']['opensearch_connection']['status'] == 'healthy'
        assert health['services']['document_processor']['status'] == 'healthy'
    
    def test_get_system_health_unhealthy(self, rag_service_with_mocks):
        """Test system health check when services are unhealthy."""
        rag_service = rag_service_with_mocks
        
        # Mock services as unhealthy
        rag_service.embedding_service.health_check.return_value = {'status': 'unhealthy'}
        rag_service.search_service.health_check.return_value = {'status': 'unhealthy'}
        rag_service.gpt_service.health_check.return_value = {'status': 'unhealthy'}
        
        health = rag_service.get_system_health()
        
        assert health['status'] == 'unhealthy'
    
    def test_get_document_statistics(self, rag_service_with_mocks):
        """Test document statistics retrieval."""
        rag_service = rag_service_with_mocks
        
        stats = rag_service.get_document_statistics()
        
        assert 'documents' in stats
        assert 'processing' in stats
        assert 'index_name' in stats
        assert 'timestamp' in stats
        
        assert stats['documents']['total_documents'] == 10
        assert stats['documents']['index_size_mb'] == 1.0
    
    def test_delete_document_success(self, rag_service_with_mocks):
        """Test successful document deletion."""
        rag_service = rag_service_with_mocks
        
        result = rag_service.delete_document("test_doc_123")
        
        assert result['success'] is True
        assert result['document_id'] == "test_doc_123"
        assert "successfully" in result['message']
        
        # Verify search service was called
        rag_service.search_service.delete_document.assert_called_once_with("test_doc_123")
    
    def test_delete_document_failure(self, rag_service_with_mocks):
        """Test document deletion failure."""
        rag_service = rag_service_with_mocks
        
        # Mock search service to return False
        rag_service.search_service.delete_document.return_value = False
        
        result = rag_service.delete_document("test_doc_123")
        
        assert result['success'] is False
        assert result['document_id'] == "test_doc_123"
        assert "Failed" in result['message']
    
    def test_delete_document_exception(self, rag_service_with_mocks):
        """Test document deletion with exception."""
        rag_service = rag_service_with_mocks
        
        # Mock search service to raise exception
        rag_service.search_service.delete_document.side_effect = Exception("Delete error")
        
        result = rag_service.delete_document("test_doc_123")
        
        assert result['success'] is False
        assert result['document_id'] == "test_doc_123"
        assert "error" in result
    
    def test_search_documents_only(self, rag_service_with_mocks):
        """Test document search without answer generation."""
        rag_service = rag_service_with_mocks
        
        # Mock embedding generation
        mock_embedding = np.random.rand(384).astype(np.float32)
        rag_service.embedding_service.get_embedding.return_value = mock_embedding
        
        # Mock search results
        mock_search_results = [
            Mock(
                content="Test content",
                document_title="Test Doc",
                score=0.9,
                chunk_id="chunk_1",
                page_number=1,
                metadata={"chunk_index": 0},
                document_id="doc_1",
                document_filename="test.pdf"
            )
        ]
        rag_service.search_service.hybrid_search.return_value = mock_search_results
        
        result = rag_service.search_documents_only("Test query")
        
        assert len(result) == 1
        assert isinstance(result[0], Source)
        assert result[0].content == "Test content"
        assert result[0].score == 0.9
    
    def test_search_documents_only_failure(self, rag_service_with_mocks):
        """Test document search failure without answer generation."""
        rag_service = rag_service_with_mocks
        
        # Mock embedding service to raise exception
        rag_service.embedding_service.get_embedding.side_effect = Exception("Embedding error")
        
        result = rag_service.search_documents_only("Test query")
        
        assert result == []
    
    def test_test_rag_pipeline_success(self, rag_service_with_mocks):
        """Test RAG pipeline test functionality."""
        rag_service = rag_service_with_mocks
        
        # Mock all services for successful test
        mock_embedding = np.random.rand(384).astype(np.float32)
        rag_service.embedding_service.get_embedding.return_value = mock_embedding
        
        mock_sources = [Source(
            content="Test content",
            document_name="Test Doc",
            score=0.9,
            chunk_id="chunk_1",
            page_number=1,
            metadata={"chunk_index": 0},
            document_id="doc_1",
            document_title="Test Document"
        )]
        rag_service.search_service.hybrid_search.return_value = mock_sources
        
        mock_response = QueryResponse(
            question="What is the main purpose of this system?",
            answer="Test answer",
            sources=mock_sources,
            search_type=SearchType.SEMANTIC,
            total_sources=1,
            tokens_used=100,
            processing_time=1.0
        )
        rag_service.gpt_service.generate_answer.return_value = mock_response
        
        result = rag_service.test_rag_pipeline()
        
        assert result['success'] is True
        assert result['test_query'] == "What is the main purpose of this system?"
        assert result['response_length'] > 0
        assert result['sources_found'] == 1
        assert result['processing_time'] > 0
        assert result['tokens_used'] == 100
    
    def test_test_rag_pipeline_failure(self, rag_service_with_mocks):
        """Test RAG pipeline test failure."""
        rag_service = rag_service_with_mocks
        
        # Mock embedding service to raise exception
        rag_service.embedding_service.get_embedding.side_effect = Exception("Test error")
        
        result = rag_service.test_rag_pipeline()
        
        assert result['success'] is False
        assert "error" in result
        assert result['test_query'] == "What is the main purpose of this system?"
    
    def test_query_processing_time_calculation(self, rag_service_with_mocks, sample_query_request):
        """Test that query processing time is calculated correctly."""
        rag_service = rag_service_with_mocks
        
        # Mock all services
        mock_embedding = np.random.rand(384).astype(np.float32)
        rag_service.embedding_service.get_embedding.return_value = mock_embedding
        rag_service.search_service.hybrid_search.return_value = []
        
        mock_response = QueryResponse(
            question=sample_query_request.question,
            answer="Test answer",
            sources=[],
            search_type=sample_query_request.search_type,
            total_sources=0,
            tokens_used=50,
            processing_time=0.5
        )
        rag_service.gpt_service.generate_answer.return_value = mock_response
        
        result = rag_service.query_documents(sample_query_request)
        
        assert result.processing_time is not None
        assert result.processing_time > 0
    
    def test_query_with_different_search_types(self, rag_service_with_mocks):
        """Test query processing with different search types."""
        rag_service = rag_service_with_mocks
        
        # Mock services
        mock_embedding = np.random.rand(384).astype(np.float32)
        rag_service.embedding_service.get_embedding.return_value = mock_embedding
        rag_service.search_service.hybrid_search.return_value = []
        
        mock_response = QueryResponse(
            question="Test question",
            answer="Test answer",
            sources=[],
            search_type=SearchType.SEMANTIC,
            total_sources=0,
            tokens_used=50,
            processing_time=0.5
        )
        rag_service.gpt_service.generate_answer.return_value = mock_response
        
        # Test semantic search
        semantic_query = QueryRequest(
            question="Test question",
            use_rag=True,
            search_type=SearchType.SEMANTIC,
            top_k=5
        )
        
        result = rag_service.query_documents(semantic_query)
        assert result.search_type == SearchType.SEMANTIC
        
        # Test keyword search
        keyword_query = QueryRequest(
            question="Test question",
            use_rag=True,
            search_type=SearchType.KEYWORD,
            top_k=5
        )
        
        result = rag_service.query_documents(keyword_query)
        assert result.search_type == SearchType.KEYWORD
