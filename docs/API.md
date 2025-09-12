# Policy Pilot API Documentation

## Overview

The Policy Pilot API provides a comprehensive RESTful interface for document management, search, and query operations. Built with FastAPI, it offers automatic OpenAPI documentation and type validation.

## Base URLs

- **Development**: `http://localhost:8000`
- **Production**: `https://api.policypilot.ai`

## Authentication

Currently, the API does not require authentication. Future versions will include API key authentication and user management.

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Document Upload**: 10 requests per minute per IP
- **Query Operations**: 50 requests per minute per IP

## Content Types

- **JSON**: `application/json`
- **Multipart**: `multipart/form-data` (for file uploads)
- **Text**: `text/plain` (for simple queries)

## Error Handling

All API responses follow a consistent error format:

```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error information",
  "status_code": 400
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Endpoints

### Health & Status

#### GET /api/health
Check overall system health.

**Response:**
```json
{
  "success": true,
  "message": "System health check completed - Status: healthy",
  "health": {
    "status": "healthy",
    "components": {
      "embedding_service": "healthy",
      "search_service": "healthy",
      "gpt_service": "healthy",
      "opensearch_connection": "healthy",
      "document_processor": "healthy"
    },
    "details": {
      "timestamp": "2024-01-15T10:30:00Z",
      "statistics": {
        "total_documents": 150,
        "total_chunks": 2500,
        "index_name": "policy_documents"
      }
    }
  }
}
```

#### GET /api/health/live
Liveness check for load balancers.

**Response:**
```json
{
  "success": true,
  "message": "System is alive",
  "alive": true,
  "status": "alive"
}
```

#### GET /api/health/ready
Readiness check for Kubernetes.

**Response:**
```json
{
  "success": true,
  "message": "System ready",
  "ready": true,
  "critical_services_healthy": true,
  "opensearch_healthy": true,
  "status": "ready"
}
```

#### GET /api/health/opensearch
Check OpenSearch connection health.

**Response:**
```json
{
  "success": true,
  "message": "OpenSearch health check completed - Status: healthy",
  "opensearch_health": {
    "status": "healthy",
    "cluster_name": "policy-pilot-cluster",
    "version": "2.11.0"
  }
}
```

#### GET /api/system-info
Get detailed system information and statistics.

**Response:**
```json
{
  "success": true,
  "message": "System information retrieved successfully",
  "system_info": {
    "system_status": "healthy",
    "services": {
      "embedding_service": "healthy",
      "search_service": "healthy",
      "gpt_service": "healthy",
      "opensearch_connection": "healthy",
      "document_processor": "healthy"
    },
    "configuration": {
      "opensearch_url": "http://localhost:9200",
      "embedding_model": "all-MiniLM-L6-v2",
      "gpt_model": "gpt-4o-mini"
    },
    "statistics": {
      "total_documents": 150,
      "total_chunks": 2500,
      "average_chunk_size": 512
    }
  }
}
```

### Document Management

#### POST /api/upload-document
Upload and process a document.

**Request:**
- **Content-Type**: `multipart/form-data`
- **Body**: Form data with file

**Parameters:**
- `file` (required): Document file (PDF, DOCX, TXT, images)

**Response:**
```json
{
  "success": true,
  "message": "Document uploaded and processed successfully",
  "document_id": "doc_123456789",
  "status": "completed",
  "chunks_created": 25,
  "processing_time": 12.5,
  "file_size": 1048576,
  "filename": "policy_document.pdf"
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Document upload failed",
  "document_id": "doc_123456789",
  "status": "failed",
  "chunks_created": 0,
  "error": "Unsupported file format",
  "file_size": 1048576,
  "filename": "policy_document.txt"
}
```

#### GET /api/documents
List all documents with pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 10, max: 100)
- `status` (optional): Filter by status (`completed`, `processing`, `failed`)
- `file_type` (optional): Filter by file type (`pdf`, `docx`, `txt`)

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 10 documents",
  "documents": [
    {
      "document_id": "doc_123456789",
      "filename": "policy_document.pdf",
      "status": "completed",
      "file_size": 1048576,
      "chunks_count": 25,
      "uploaded_at": "2024-01-15T10:30:00Z",
      "processed_at": "2024-01-15T10:32:00Z"
    }
  ],
  "total_count": 150,
  "page": 1,
  "page_size": 10,
  "total_pages": 15,
  "has_next": true,
  "has_previous": false
}
```

#### GET /api/documents/{document_id}
Get detailed information about a specific document.

**Path Parameters:**
- `document_id` (required): Document identifier

**Response:**
```json
{
  "success": true,
  "message": "Document details retrieved",
  "document": {
    "document_id": "doc_123456789",
    "filename": "policy_document.pdf",
    "status": "completed",
    "file_size": 1048576,
    "chunks_count": 25,
    "uploaded_at": "2024-01-15T10:30:00Z",
    "processed_at": "2024-01-15T10:32:00Z",
    "metadata": {
      "title": "Company Policy Document",
      "author": "HR Department",
      "pages": 15
    }
  },
  "chunks": [
    {
      "chunk_id": "chunk_001",
      "content": "This document outlines the company's remote work policy...",
      "page_number": 1,
      "score": 0.95
    }
  ]
}
```

#### DELETE /api/documents/{document_id}
Delete a document and all its chunks.

**Path Parameters:**
- `document_id` (required): Document identifier

**Response:**
```json
{
  "success": true,
  "message": "Document deleted successfully",
  "document_id": "doc_123456789",
  "chunks_deleted": 25
}
```

#### GET /api/documents/{document_id}/chunks
Get all chunks for a specific document.

**Path Parameters:**
- `document_id` (required): Document identifier

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 10, max: 100)

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 25 chunks for document doc_123456789",
  "document_id": "doc_123456789",
  "chunks": [
    {
      "chunk_id": "chunk_001",
      "content": "This document outlines the company's remote work policy...",
      "page_number": 1,
      "score": 0.95,
      "metadata": {
        "section": "Introduction",
        "word_count": 150
      }
    }
  ],
  "page": 1,
  "page_size": 10,
  "total_chunks": 25
}
```

#### GET /api/documents/stats
Get comprehensive document statistics.

**Response:**
```json
{
  "success": true,
  "message": "Document statistics retrieved",
  "statistics": {
    "documents": {
      "total_documents": 150,
      "completed": 145,
      "processing": 3,
      "failed": 2,
      "by_type": {
        "pdf": 120,
        "docx": 25,
        "txt": 5
      }
    },
    "chunks": {
      "total_chunks": 2500,
      "average_chunk_size": 512,
      "total_words": 125000
    },
    "storage": {
      "total_size_bytes": 52428800,
      "average_document_size": 349525
    }
  }
}
```

### Query & Search

#### POST /api/query
Query the RAG system with a question.

**Request Body:**
```json
{
  "question": "What is the company's remote work policy?",
  "use_rag": true,
  "search_type": "semantic",
  "top_k": 5,
  "min_score": 0.7,
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Parameters:**
- `question` (required): The question to ask
- `use_rag` (optional): Whether to use RAG mode (default: true)
- `search_type` (optional): Search type - `semantic`, `keyword`, `hybrid` (default: semantic)
- `top_k` (optional): Number of relevant documents to retrieve (default: 5, max: 20)
- `min_score` (optional): Minimum relevance score (default: 0.0)
- `temperature` (optional): GPT temperature (default: 0.7)
- `max_tokens` (optional): Maximum tokens for response (default: 1000)

**Response:**
```json
{
  "success": true,
  "message": "Query processed successfully",
  "query_response": {
    "question": "What is the company's remote work policy?",
    "answer": "Based on the company policy document, the remote work policy allows employees to work from home up to 3 days per week with manager approval. Employees must have a dedicated workspace and reliable internet connection...",
    "sources": [
      {
        "content": "Remote Work Policy: Employees may work from home up to 3 days per week...",
        "document_name": "company_policy.pdf",
        "page_number": 5,
        "score": 0.95,
        "chunk_id": "chunk_123"
      }
    ],
    "total_sources": 3,
    "processing_time": 2.5,
    "model_used": "gpt-4o-mini",
    "tokens_used": 450
  }
}
```

#### POST /api/search
Search documents without generating an answer.

**Request Body:**
```json
{
  "query": "remote work policy",
  "search_type": "semantic",
  "top_k": 10,
  "min_score": 0.7
}
```

**Parameters:**
- `query` (required): Search query
- `search_type` (optional): Search type - `semantic`, `keyword`, `hybrid` (default: semantic)
- `top_k` (optional): Number of results to return (default: 10, max: 50)
- `min_score` (optional): Minimum relevance score (default: 0.0)

**Response:**
```json
{
  "success": true,
  "message": "Found 8 relevant documents",
  "search_response": {
    "query": "remote work policy",
    "results": [
      {
        "content": "Remote Work Policy: Employees may work from home up to 3 days per week...",
        "document_name": "company_policy.pdf",
        "page_number": 5,
        "score": 0.95,
        "chunk_id": "chunk_123"
      }
    ],
    "total_results": 8,
    "search_type": "semantic",
    "processing_time": 0.8
  }
}
```

#### GET /api/query/simple
Simple query endpoint with query string parameters.

**Query Parameters:**
- `q` (required): Query question
- `use_rag` (optional): Use RAG mode (default: true)
- `search_type` (optional): Search type (default: semantic)
- `top_k` (optional): Number of results (default: 5, max: 20)

**Example:**
```
GET /api/query/simple?q=What is the refund policy?&use_rag=true&top_k=3
```

**Response:**
```json
{
  "success": true,
  "question": "What is the refund policy?",
  "answer": "The refund policy allows customers to return products within 30 days...",
  "sources": [
    {
      "content": "Refund Policy: Customers may return products within 30 days...",
      "document_name": "return_policy.pdf",
      "score": 0.92,
      "page_number": 3
    }
  ],
  "total_sources": 2,
  "processing_time": 1.8,
  "model_used": "gpt-4o-mini",
  "tokens_used": 320
}
```

#### GET /api/search/simple
Simple search endpoint with query string parameters.

**Query Parameters:**
- `q` (required): Search query
- `search_type` (optional): Search type (default: semantic)
- `top_k` (optional): Number of results (default: 10, max: 50)
- `min_score` (optional): Minimum relevance score (default: 0.0)

**Example:**
```
GET /api/search/simple?q=remote work&search_type=semantic&top_k=5&min_score=0.8
```

**Response:**
```json
{
  "success": true,
  "query": "remote work",
  "results": [
    {
      "content": "Remote Work Policy: Employees may work from home up to 3 days per week...",
      "document_name": "company_policy.pdf",
      "score": 0.95,
      "page_number": 5,
      "chunk_id": "chunk_123"
    }
  ],
  "total_results": 5,
  "search_type": "semantic"
}
```

#### POST /api/query/test
Test the complete RAG pipeline.

**Response:**
```json
{
  "success": true,
  "message": "RAG pipeline test completed",
  "test_results": {
    "embedding_service": "healthy",
    "search_service": "healthy",
    "gpt_service": "healthy",
    "opensearch_connection": "healthy",
    "document_processor": "healthy",
    "test_query": "What is the company policy?",
    "test_response": "The company policy includes guidelines for...",
    "processing_time": 1.2
  }
}
```

#### GET /api/query/supported-search-types
Get list of supported search types.

**Response:**
```json
{
  "success": true,
  "message": "Supported search types retrieved",
  "search_types": [
    {
      "value": "semantic",
      "name": "SEMANTIC",
      "description": "Semantic search"
    },
    {
      "value": "keyword",
      "name": "KEYWORD",
      "description": "Keyword search"
    },
    {
      "value": "hybrid",
      "name": "HYBRID",
      "description": "Hybrid search"
    }
  ]
}
```

## Data Models

### Document Status
```json
{
  "completed": "Document processed successfully",
  "processing": "Document is being processed",
  "failed": "Document processing failed",
  "pending": "Document waiting to be processed"
}
```

### Search Types
```json
{
  "semantic": "Semantic similarity search using embeddings",
  "keyword": "Traditional keyword-based search",
  "hybrid": "Combination of semantic and keyword search"
}
```

### Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `FILE_TOO_LARGE` | Uploaded file exceeds size limit | Reduce file size or split document |
| `UNSUPPORTED_FORMAT` | File format not supported | Convert to PDF, DOCX, or TXT |
| `PROCESSING_FAILED` | Document processing failed | Check file integrity and try again |
| `OPENSEARCH_ERROR` | OpenSearch connection failed | Check OpenSearch service status |
| `OPENAI_ERROR` | OpenAI API error | Check API key and rate limits |
| `VALIDATION_ERROR` | Request validation failed | Check request parameters |

## Examples

### Complete Workflow

1. **Upload a document:**
```bash
curl -X POST "http://localhost:8000/api/upload-document" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@policy_document.pdf"
```

2. **Query the system:**
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key points about data privacy?",
    "use_rag": true,
    "search_type": "semantic",
    "top_k": 5
  }'
```

3. **Search for specific content:**
```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "data privacy policy",
    "search_type": "semantic",
    "top_k": 10,
    "min_score": 0.8
  }'
```

4. **Check system health:**
```bash
curl "http://localhost:8000/api/health"
```

### Python Client Example

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# Upload document
def upload_document(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/api/upload-document", files=files)
    return response.json()

# Query documents
def query_documents(question):
    data = {
        "question": question,
        "use_rag": True,
        "search_type": "semantic",
        "top_k": 5
    }
    response = requests.post(f"{BASE_URL}/api/query", json=data)
    return response.json()

# Search documents
def search_documents(query):
    data = {
        "query": query,
        "search_type": "semantic",
        "top_k": 10,
        "min_score": 0.7
    }
    response = requests.post(f"{BASE_URL}/api/search", json=data)
    return response.json()

# Example usage
if __name__ == "__main__":
    # Upload a document
    upload_result = upload_document("policy_document.pdf")
    print("Upload result:", upload_result)
    
    # Query the system
    query_result = query_documents("What is the company's remote work policy?")
    print("Query result:", query_result)
    
    # Search for content
    search_result = search_documents("remote work policy")
    print("Search result:", search_result)
```

### JavaScript Client Example

```javascript
const BASE_URL = 'http://localhost:8000';

// Upload document
async function uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${BASE_URL}/api/upload-document`, {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}

// Query documents
async function queryDocuments(question) {
    const response = await fetch(`${BASE_URL}/api/query`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question: question,
            use_rag: true,
            search_type: 'semantic',
            top_k: 5
        })
    });
    
    return await response.json();
}

// Search documents
async function searchDocuments(query) {
    const response = await fetch(`${BASE_URL}/api/search`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: query,
            search_type: 'semantic',
            top_k: 10,
            min_score: 0.7
        })
    });
    
    return await response.json();
}

// Example usage
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const file = document.getElementById('fileInput').files[0];
    const result = await uploadDocument(file);
    console.log('Upload result:', result);
});

document.getElementById('queryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = document.getElementById('questionInput').value;
    const result = await queryDocuments(question);
    console.log('Query result:', result);
});
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **General API**: 100 requests per minute per IP
- **Document Upload**: 10 requests per minute per IP
- **Query Operations**: 50 requests per minute per IP

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Webhooks (Future Feature)

Future versions will support webhooks for:
- Document processing completion
- System health alerts
- Error notifications

## SDKs (Future Feature)

Future versions will include official SDKs for:
- Python
- JavaScript/Node.js
- Java
- C#

## Support

For API support and questions:
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/policy-pilot/issues)
- **Email**: api-support@policypilot.ai
