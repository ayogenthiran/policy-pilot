# Testing Infrastructure

This document describes the comprehensive testing infrastructure for the Policy Pilot RAG backend system.

## Overview

The testing suite provides confidence that all components work correctly individually and together, covering:

- **Unit Tests**: Individual component testing with mocked dependencies
- **Integration Tests**: End-to-end testing with real services
- **API Tests**: HTTP endpoint testing
- **Performance Tests**: Load and performance benchmarking
- **Sample Data Tests**: Real document processing verification

## Test Structure

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── test_document_processor.py  # Document processing unit tests
└── test_rag_service.py         # RAG service integration tests

scripts/
├── test_integration.py         # End-to-end integration testing
├── load_sample_data.py         # Sample data loading and verification
└── run_tests.py               # Comprehensive test runner
```

## Quick Start

### 1. Install Dependencies

```bash
# Install development dependencies
make install-dev
# or
pip install -e ".[dev]"
```

### 2. Run Tests

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-api

# Run with coverage
make test-coverage
```

### 3. Run Integration Tests

```bash
# Start the server
make run-server

# In another terminal, run integration tests
make run-integration
```

### 4. Load Sample Data

```bash
# Load sample policy documents
make run-sample-data
```

## Test Categories

### Unit Tests

Unit tests focus on individual components with mocked dependencies:

- **Document Processor Tests** (`test_document_processor.py`)
  - PDF, DOCX, TXT processing
  - Document chunking with different configurations
  - Embedding generation and indexing
  - Error handling and edge cases

- **RAG Service Tests** (`test_rag_service.py`)
  - Complete RAG pipeline testing
  - Query processing with and without RAG
  - Error handling and edge cases
  - Response format validation

### Integration Tests

Integration tests verify components work together:

- **API Integration** (`test_integration.py`)
  - Document upload via HTTP API
  - Query processing via HTTP API
  - Health check endpoints
  - Performance benchmarking

- **Service Integration**
  - Real OpenSearch indexing
  - Actual embedding generation
  - Complete document processing pipeline

### API Tests

API tests verify HTTP endpoints:

- **Document Management**
  - Upload documents
  - List documents
  - Get document details
  - Delete documents

- **Query Processing**
  - RAG-enabled queries
  - Direct queries
  - Error handling

- **System Health**
  - Health check endpoints
  - Statistics endpoints

## Test Fixtures

The `conftest.py` file provides comprehensive fixtures:

### Mock Services

- `mock_embedding_service`: Mocked embedding generation
- `mock_search_service`: Mocked OpenSearch operations
- `mock_gpt_service`: Mocked GPT answer generation
- `mock_file_service`: Mocked file operations

### Test Data

- `sample_document_metadata`: Sample document metadata
- `sample_document_chunks`: Sample document chunks
- `sample_processed_document`: Complete processed document
- `sample_query_request`: Sample query request
- `sample_query_response`: Sample query response
- `sample_test_files`: Test document files (PDF, TXT)

### Test Environment

- `test_data_dir`: Temporary directory for test data
- `test_uploads_dir`: Temporary directory for uploads
- `test_documents_dir`: Temporary directory for documents
- `test_client`: FastAPI test client

## Running Tests

### Using Make

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-api

# Run with coverage
make test-coverage

# Run with verbose output
make test-verbose
```

### Using pytest directly

```bash
# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_document_processor.py
pytest tests/test_rag_service.py

# Run with markers
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m api

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific tests
pytest tests/test_document_processor.py::TestDocumentProcessor::test_process_document_success
```

### Using the test runner

```bash
# Run comprehensive test suite
python scripts/run_tests.py --all --verbose

# Run specific test types
python scripts/run_tests.py --unit
python scripts/run_tests.py --integration
python scripts/run_tests.py --api

# Run with custom options
python scripts/run_tests.py --all --no-coverage --no-linting
```

## Integration Testing

### Prerequisites

1. Start the API server:
   ```bash
   make run-server
   ```

2. Ensure OpenSearch is running (if using real services)

### Running Integration Tests

```bash
# Run integration tests with test documents
python scripts/test_integration.py --create-test-docs

# Run with custom documents
python scripts/test_integration.py --test-docs path/to/doc1.pdf path/to/doc2.txt

# Run performance tests
python scripts/test_integration.py --performance-queries 20

# Save results to file
python scripts/test_integration.py --output integration_results.json
```

### Integration Test Features

- **Health Check**: Verify API is running and healthy
- **Document Upload**: Test file upload and processing
- **Query Processing**: Test RAG and direct queries
- **Document Management**: Test listing, details, and deletion
- **Performance Benchmarking**: Test with multiple queries
- **Error Handling**: Test various error scenarios

## Sample Data Loading

### Loading Sample Documents

```bash
# Create and load sample documents
python scripts/load_sample_data.py --create-sample

# Load custom documents
python scripts/load_sample_data.py --documents doc1.pdf doc2.txt

# Run custom test queries
python scripts/load_sample_data.py --queries "What is the privacy policy?" "How to handle security incidents?"
```

### Sample Documents

The system includes sample policy documents:

1. **Data Privacy Policy**: GDPR-compliant privacy policy
2. **Remote Work Policy**: Guidelines for remote work
3. **Information Security Policy**: Security procedures and requirements
4. **Code of Conduct**: Employee behavior and ethics guidelines

## Test Configuration

### Pytest Configuration

The `pyproject.toml` file contains pytest configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
```

### Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.api`: API tests
- `@pytest.mark.slow`: Slow-running tests

### Coverage Configuration

Coverage reports are generated in multiple formats:

- **Terminal**: Shows missing lines
- **HTML**: Interactive HTML report in `htmlcov/`
- **XML**: Machine-readable report in `coverage.xml`

## Continuous Integration

### GitHub Actions

The test suite is designed to run in CI/CD pipelines:

```yaml
- name: Run Tests
  run: |
    make install-dev
    make test-coverage
    make lint

- name: Run Integration Tests
  run: |
    make run-server &
    sleep 10
    make run-integration
```

### Test Reports

Test results are saved in multiple formats:

- **JSON**: Machine-readable test results
- **XML**: JUnit-compatible test results
- **HTML**: Interactive coverage reports

## Debugging Tests

### Running Specific Tests

```bash
# Run specific test method
pytest tests/test_document_processor.py::TestDocumentProcessor::test_process_document_success -v

# Run tests matching pattern
pytest tests/ -k "test_process_document" -v

# Run tests with debugging
pytest tests/ -v -s --pdb
```

### Test Debugging Tips

1. **Use verbose output**: `-v` flag shows individual test names
2. **Use print statements**: `-s` flag shows print output
3. **Use debugger**: `--pdb` flag drops into debugger on failure
4. **Check fixtures**: Verify mock services are working correctly
5. **Check test data**: Ensure sample data is properly loaded

## Performance Testing

### Load Testing

```bash
# Run performance tests
python scripts/test_integration.py --performance-queries 50

# Run with custom server
python scripts/test_integration.py --base-url http://localhost:8000 --performance-queries 100
```

### Performance Metrics

The test suite measures:

- **Query Response Time**: Average time per query
- **Throughput**: Queries per second
- **Memory Usage**: Peak memory consumption
- **Document Processing Time**: Time to process documents
- **Indexing Performance**: Time to index documents

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **Mock Failures**: Check mock service configurations
3. **Test Data Issues**: Verify test files exist and are readable
4. **API Connection**: Ensure server is running for integration tests
5. **OpenSearch Issues**: Check OpenSearch connection and configuration

### Test Environment

Ensure the test environment is properly set up:

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Check dependencies
pip list | grep pytest

# Check test discovery
pytest --collect-only tests/
```

## Best Practices

### Writing Tests

1. **Use descriptive test names**: Clearly indicate what is being tested
2. **Test one thing at a time**: Each test should verify one specific behavior
3. **Use appropriate fixtures**: Leverage existing fixtures for common setup
4. **Mock external dependencies**: Isolate units under test
5. **Test edge cases**: Include error conditions and boundary cases

### Test Organization

1. **Group related tests**: Use test classes for related functionality
2. **Use meaningful markers**: Categorize tests with appropriate markers
3. **Keep tests independent**: Tests should not depend on each other
4. **Clean up after tests**: Use fixtures for proper cleanup
5. **Document test purpose**: Add docstrings explaining test intent

### Maintenance

1. **Keep tests up to date**: Update tests when code changes
2. **Remove obsolete tests**: Delete tests for removed functionality
3. **Monitor test performance**: Keep test execution time reasonable
4. **Review test coverage**: Ensure adequate coverage of critical paths
5. **Refactor test code**: Keep test code clean and maintainable

## Contributing

When adding new tests:

1. **Follow naming conventions**: Use `test_` prefix for test functions
2. **Add appropriate markers**: Mark tests with correct categories
3. **Update fixtures**: Add new fixtures to `conftest.py` if needed
4. **Document test purpose**: Add docstrings explaining test intent
5. **Ensure test isolation**: Tests should not depend on external state

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
