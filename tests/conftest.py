"""
Simple pytest configuration and fixtures for Policy Pilot RAG backend tests.
This version doesn't import the main app to avoid dependency issues.
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

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


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
    mock_service = Mock()
    
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
def sample_test_files(test_documents_dir):
    """Create sample test files for testing."""
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
