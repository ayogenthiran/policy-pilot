"""
Pytest configuration and fixtures for Policy Pilot RAG backend tests.
Provides test database setup, mock services, and test data fixtures.
"""

import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pytest
import numpy as np
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.main import app
from src.config.settings import settings
from src.models.document import (
    DocumentStatus, DocumentMetadata, DocumentChunk, ProcessedDocument,
    DocumentSummary, DocumentSearchResult
)
from src.models.query import QueryRequest, QueryResponse, SearchType, Source
from src.services.rag_service import RAGService
from src.services.document_processor import DocumentProcessor
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService
from src.services.gpt_service import GPTService
from src.services.file_service import FileService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp(prefix="policy_pilot_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def test_uploads_dir(test_data_dir):
    """Create a temporary directory for test uploads."""
    uploads_dir = test_data_dir / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    return uploads_dir


@pytest.fixture(scope="session")
def test_documents_dir(test_data_dir):
    """Create a temporary directory for test documents."""
    docs_dir = test_data_dir / "documents"
    docs_dir.mkdir(exist_ok=True)
    return docs_dir


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing."""
    mock_service = Mock(spec=EmbeddingService)
    
    # Mock embedding generation
    def mock_get_embedding(text: str) -> np.ndarray:
        # Return a consistent 384-dimensional vector
        np.random.seed(hash(text) % 2**32)
        return np.random.rand(384).astype(np.float32)
    
    def mock_get_embeddings_batch(texts: List[str]) -> List[np.ndarray]:
        return [mock_get_embedding(text) for text in texts]
    
    mock_service.get_embedding.side_effect = mock_get_embedding
    mock_service.get_embeddings_batch.side_effect = mock_get_embeddings_batch
    
    # Mock health check
    mock_service.health_check.return_value = {
        'status': 'healthy',
        'model_name': 'test-model',
        'embedding_dimension': 384
    }
    
    # Mock model info
    mock_service.get_model_info.return_value = {
        'model_name': 'test-model',
        'embedding_dimension': 384,
        'max_tokens': 512
    }
    
    return mock_service


@pytest.fixture
def mock_search_service():
    """Mock search service for testing."""
    mock_service = Mock(spec=SearchService)
    
    # Mock search results
    def mock_hybrid_search(query: str, query_embedding: np.ndarray, 
                          search_type: SearchType = SearchType.SEMANTIC,
                          top_k: int = 10, min_score: float = 0.0) -> List[DocumentSearchResult]:
        # Return mock search results
        results = []
        for i in range(min(top_k, 3)):  # Return up to 3 mock results
            result = DocumentSearchResult(
                chunk_id=f"chunk_{i}",
                document_id=f"doc_{i}",
                content=f"Mock content for query: {query}",
                score=0.9 - (i * 0.1),
                page_number=i + 1,
                metadata={"chunk_index": i, "word_count": 50},
                document_title=f"Test Document {i}",
                document_filename=f"test_doc_{i}.pdf"
            )
            results.append(result)
        return results
    
    mock_service.hybrid_search.side_effect = mock_hybrid_search
    
    # Mock indexing
    mock_service.index_documents.return_value = {
        'success': True,
        'indexed_count': 5,
        'failed_count': 0
    }
    
    # Mock document deletion
    mock_service.delete_document.return_value = True
    
    # Mock health check
    mock_service.health_check.return_value = {
        'status': 'healthy',
        'index_name': 'test_index',
        'document_count': 10
    }
    
    # Mock document stats
    mock_service.get_document_stats.return_value = {
        'total_documents': 10,
        'index_size_bytes': 1024000,
        'index_size_mb': 1.0,
        'index_name': 'test_index'
    }
    
    return mock_service


@pytest.fixture
def mock_gpt_service():
    """Mock GPT service for testing."""
    mock_service = Mock(spec=GPTService)
    
    # Mock answer generation
    def mock_generate_answer(query_request: QueryRequest, sources: List[Source]) -> QueryResponse:
        return QueryResponse(
            question=query_request.question,
            answer=f"Mock answer for: {query_request.question}",
            sources=sources,
            search_type=query_request.search_type,
            total_sources=len(sources),
            tokens_used=100,
            processing_time=0.5
        )
    
    mock_service.generate_answer.side_effect = mock_generate_answer
    
    # Mock health check
    mock_service.health_check.return_value = {
        'status': 'healthy',
        'model_name': 'test-gpt-model',
        'max_tokens': 4096
    }
    
    # Mock model info
    mock_service.get_model_info.return_value = {
        'model_name': 'test-gpt-model',
        'max_tokens': 4096,
        'temperature': 0.7
    }
    
    return mock_service


@pytest.fixture
def mock_file_service():
    """Mock file service for testing."""
    mock_service = Mock(spec=FileService)
    
    # Mock file validation
    mock_service.validate_file.return_value = {
        'valid': True,
        'file_type': 'application/pdf',
        'size_mb': 1.0
    }
    
    # Mock file saving
    def mock_save_uploaded_file(file_content: bytes, filename: str) -> Dict[str, Any]:
        return {
            'file_path': f"/tmp/test_{filename}",
            'document_id': f"doc_{hash(filename)}",
            'filename': filename
        }
    
    mock_service.save_uploaded_file.side_effect = mock_save_uploaded_file
    
    # Mock document ID generation
    mock_service.generate_document_id.return_value = "test_doc_id"
    
    return mock_service


@pytest.fixture
def mock_document_loader():
    """Mock document loader for testing."""
    with patch('src.services.document_processor.DocumentLoader') as mock_loader:
        mock_instance = Mock()
        
        # Mock document loading
        def mock_load_document(file_path: Path, file_type: str) -> Dict[str, Any]:
            return {
                'text_content': [
                    "This is a test document with multiple paragraphs.",
                    "It contains important policy information.",
                    "The document has several sections with different topics."
                ],
                'metadata': {
                    'title': 'Test Policy Document',
                    'author': 'Test Author',
                    'total_pages': 3,
                    'language': 'en',
                    'extraction_method': 'test'
                }
            }
        
        mock_instance.load_document.side_effect = mock_load_document
        mock_loader.return_value = mock_instance
        
        yield mock_instance


@pytest.fixture
def mock_text_chunker():
    """Mock text chunker for testing."""
    with patch('src.services.document_processor.TextChunker') as mock_chunker:
        mock_instance = Mock()
        
        # Mock document chunking
        def mock_chunk_document(document_data: Dict[str, Any], document_id: str) -> List[Dict[str, Any]]:
            chunks = []
            text_content = document_data.get('text_content', [])
            
            for i, text in enumerate(text_content):
                chunk = {
                    'chunk_id': f"{document_id}_chunk_{i}",
                    'content': text,
                    'metadata': {
                        'chunk_index': i,
                        'document_id': document_id,
                        'page_number': i + 1
                    },
                    'page_number': i + 1,
                    'word_count': len(text.split()),
                    'char_count': len(text)
                }
                chunks.append(chunk)
            
            return chunks
        
        mock_instance.chunk_document.side_effect = mock_chunk_document
        mock_instance.chunk_size = 1000
        mock_instance.chunk_overlap = 200
        mock_chunker.return_value = mock_instance
        
        yield mock_instance


@pytest.fixture
def sample_document_metadata():
    """Sample document metadata for testing."""
    return DocumentMetadata(
        title="Test Policy Document",
        author="Test Author",
        file_size=1024000,
        file_type="application/pdf",
        total_pages=5,
        language="en",
        tags=["policy", "test"],
        description="A test policy document for unit testing",
        custom_metadata={
            'extraction_method': 'test',
            'total_elements': 3
        }
    )


@pytest.fixture
def sample_document_chunks():
    """Sample document chunks for testing."""
    chunks = []
    for i in range(3):
        chunk = DocumentChunk(
            chunk_id=f"test_chunk_{i}",
            content=f"This is test chunk {i} with some content for testing purposes.",
            metadata={
                'chunk_index': i,
                'document_id': 'test_doc',
                'page_number': i + 1
            },
            page_number=i + 1,
            chunk_index=i,
            word_count=15,
            char_count=70
        )
        chunks.append(chunk)
    return chunks


@pytest.fixture
def sample_processed_document(sample_document_metadata, sample_document_chunks):
    """Sample processed document for testing."""
    return ProcessedDocument(
        document_id="test_doc_123",
        filename="test_document.pdf",
        status=DocumentStatus.COMPLETED,
        chunks_count=len(sample_document_chunks),
        created_at=1234567890.0,
        completed_at=1234567895.0,
        processing_time_seconds=5.0,
        metadata=sample_document_metadata,
        chunks=sample_document_chunks
    )


@pytest.fixture
def sample_query_request():
    """Sample query request for testing."""
    return QueryRequest(
        question="What is the main purpose of this policy?",
        use_rag=True,
        search_type=SearchType.SEMANTIC,
        top_k=5,
        min_score=0.7
    )


@pytest.fixture
def sample_query_response():
    """Sample query response for testing."""
    return QueryResponse(
        question="What is the main purpose of this policy?",
        answer="The main purpose of this policy is to establish guidelines for testing.",
        sources=[
            Source(
                content="This policy establishes testing guidelines.",
                document_name="Test Policy Document",
                score=0.95,
                chunk_id="chunk_1",
                page_number=1,
                metadata={"chunk_index": 0},
                document_id="test_doc",
                document_title="Test Policy Document"
            )
        ],
        search_type=SearchType.SEMANTIC,
        total_sources=1,
        processing_time=1.5,
        tokens_used=150
    )


@pytest.fixture
def sample_test_files(test_documents_dir):
    """Create sample test files for testing."""
    # Create sample PDF content (simplified)
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Policy Document) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF"""
    
    # Create sample text content
    txt_content = """Test Policy Document

This is a test policy document for unit testing purposes.
It contains multiple paragraphs with different information.

Section 1: Introduction
This section introduces the policy and its objectives.

Section 2: Guidelines
This section outlines the specific guidelines to follow.

Section 3: Implementation
This section describes how to implement the policy.
"""
    
    # Create test files
    test_files = {}
    
    # PDF file
    pdf_file = test_documents_dir / "test_policy.pdf"
    pdf_file.write_bytes(pdf_content)
    test_files['pdf'] = str(pdf_file)
    
    # TXT file
    txt_file = test_documents_dir / "test_policy.txt"
    txt_file.write_text(txt_content)
    test_files['txt'] = str(txt_file)
    
    # Create a larger text file for chunking tests
    large_txt_content = "\n".join([f"Paragraph {i}: This is paragraph number {i} with some content for testing chunking functionality." for i in range(50)])
    large_txt_file = test_documents_dir / "large_test_document.txt"
    large_txt_file.write_text(large_txt_content)
    test_files['large_txt'] = str(large_txt_file)
    
    return test_files


@pytest.fixture
def mock_opensearch_connection():
    """Mock OpenSearch connection for testing."""
    with patch('src.config.database.opensearch_connection') as mock_conn:
        mock_conn.health_check.return_value = {
            'status': 'healthy',
            'cluster_name': 'test_cluster',
            'version': '2.3.0'
        }
        yield mock_conn


@pytest.fixture
def test_client():
    """Create a test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def rag_service_with_mocks(mock_embedding_service, mock_search_service, 
                          mock_gpt_service, mock_file_service, 
                          mock_document_loader, mock_text_chunker,
                          mock_opensearch_connection):
    """Create RAG service with all mocked dependencies."""
    with patch('src.services.rag_service.EmbeddingService', return_value=mock_embedding_service), \
         patch('src.services.rag_service.SearchService', return_value=mock_search_service), \
         patch('src.services.rag_service.GPTService', return_value=mock_gpt_service), \
         patch('src.services.rag_service.DocumentProcessor') as mock_processor_class:
        
        # Create mock document processor
        mock_processor = Mock(spec=DocumentProcessor)
        mock_processor.health_check.return_value = {'status': 'healthy'}
        mock_processor.get_processing_stats.return_value = {
            'embedding_service': {'status': 'healthy'},
            'search_service': {'status': 'healthy'},
            'chunk_size': 1000,
            'chunk_overlap': 200
        }
        mock_processor_class.return_value = mock_processor
        
        # Create RAG service
        rag_service = RAGService()
        rag_service.embedding_service = mock_embedding_service
        rag_service.search_service = mock_search_service
        rag_service.gpt_service = mock_gpt_service
        rag_service.document_processor = mock_processor
        
        return rag_service


@pytest.fixture
def document_processor_with_mocks(mock_embedding_service, mock_search_service,
                                 mock_file_service, mock_document_loader,
                                 mock_text_chunker):
    """Create document processor with all mocked dependencies."""
    with patch('src.services.document_processor.EmbeddingService', return_value=mock_embedding_service), \
         patch('src.services.document_processor.SearchService', return_value=mock_search_service), \
         patch('src.services.document_processor.FileService', return_value=mock_file_service):
        
        # Create document processor
        processor = DocumentProcessor()
        processor.embedding_service = mock_embedding_service
        processor.search_service = mock_search_service
        processor.file_service = mock_file_service
        processor.document_loader = mock_document_loader
        processor.text_chunker = mock_text_chunker
        
        return processor


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add unit marker to tests in test_*_unit.py files
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to tests in test_*_integration.py files
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests with "slow" in the name
        if "slow" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Add api marker to tests in test_api.py files
        if "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
