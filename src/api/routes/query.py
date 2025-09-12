"""
Query API routes for Policy Pilot RAG backend.
Handles document queries and search operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query as FastAPIQuery
from fastapi.responses import JSONResponse

from src.core.logging import get_logger
from src.services.rag_service import RAGService
from src.models.query import QueryRequest, QueryResponse, SearchRequest, SearchResponse, SearchType
from src.models.schemas import QueryAPIResponse, SearchAPIResponse
from src.utils.exceptions import GPTServiceError, SearchServiceError, EmbeddingServiceError
from src.utils.security import security_validator
from src.utils.metrics import structured_logger, metrics_collector

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["query"])


def get_rag_service() -> RAGService:
    """Dependency to get RAG service instance."""
    return RAGService()


@router.post(
    "/query",
    response_model=QueryAPIResponse,
    summary="Query documents",
    description="Query the RAG system with a question and get an answer with sources"
)
async def query_documents(
    query_request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service)
) -> QueryAPIResponse:
    """
    Query the RAG system with a question.
    
    Args:
        query_request: Query request with question and parameters
        rag_service: RAG service dependency
        
    Returns:
        Query response with answer and sources
    """
    try:
        # Security validation
        query_validation = security_validator.validate_query(query_request.question)
        if not query_validation['valid']:
            raise HTTPException(status_code=400, detail=f"Query validation failed: {query_validation}")
        
        # Use sanitized query
        query_request.question = query_validation['sanitized_query']
        
        logger.info(f"Processing query: {query_request.question[:100]}...")
        
        # Execute RAG pipeline
        import time
        start_time = time.time()
        query_response = rag_service.query_documents(query_request)
        
        processing_time = time.time() - start_time
        
        # Record metrics
        metrics_collector.record_metric(
            operation="query_processing",
            duration=processing_time,
            success=query_response.error is None,
            metadata={
                "question_length": len(query_request.question),
                "sources_count": len(query_response.sources),
                "use_rag": query_request.use_rag,
                "search_type": query_request.search_type.value if query_request.search_type else None
            }
        )
        
        # Log structured query
        structured_logger.log_search_query(
            query=query_request.question,
            results_count=len(query_response.sources),
            duration=processing_time,
            search_type="rag_query" if query_request.use_rag else "direct_query",
            success=query_response.error is None,
            error=query_response.error
        )
        
        # Create API response
        api_response = QueryAPIResponse(
            success=True,
            message="Query processed successfully",
            query_response=query_response
        )
        
        logger.info(
            f"Query completed: {len(query_response.sources)} sources, "
            f"{query_response.processing_time:.2f}s"
        )
        
        return api_response
        
    except GPTServiceError as e:
        logger.error(f"GPT service error during query: {e}")
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except SearchServiceError as e:
        logger.error(f"Search service error during query: {e}")
        raise HTTPException(status_code=503, detail=f"Search service error: {str(e)}")
    except EmbeddingServiceError as e:
        logger.error(f"Embedding service error during query: {e}")
        raise HTTPException(status_code=503, detail=f"Embedding service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/search",
    response_model=SearchAPIResponse,
    summary="Search documents",
    description="Search documents without generating an answer"
)
async def search_documents(
    search_request: SearchRequest,
    rag_service: RAGService = Depends(get_rag_service)
) -> SearchAPIResponse:
    """
    Search documents without generating an answer.
    
    Args:
        search_request: Search request with query and parameters
        rag_service: RAG service dependency
        
    Returns:
        Search response with relevant documents
    """
    try:
        logger.info(f"Processing search: {search_request.query[:100]}...")
        
        # Execute search
        sources = rag_service.search_documents_only(
            query=search_request.query,
            search_type=search_request.search_type,
            top_k=search_request.top_k,
            min_score=search_request.min_score
        )
        
        # Create search response
        search_response = SearchResponse(
            query=search_request.query,
            results=sources,
            total_results=len(sources),
            search_type=search_request.search_type,
            processing_time=0.0  # This would be measured in the service
        )
        
        # Create API response
        api_response = SearchAPIResponse(
            success=True,
            message=f"Found {len(sources)} relevant documents",
            search_response=search_response
        )
        
        logger.info(f"Search completed: {len(sources)} results")
        return api_response
        
    except SearchServiceError as e:
        logger.error(f"Search service error: {e}")
        raise HTTPException(status_code=503, detail=f"Search service error: {str(e)}")
    except EmbeddingServiceError as e:
        logger.error(f"Embedding service error: {e}")
        raise HTTPException(status_code=503, detail=f"Embedding service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/query/simple",
    summary="Simple query",
    description="Simple query endpoint with query string parameter"
)
async def simple_query(
    q: str = FastAPIQuery(..., description="Query question"),
    use_rag: bool = FastAPIQuery(True, description="Use RAG mode"),
    search_type: SearchType = FastAPIQuery(SearchType.SEMANTIC, description="Search type"),
    top_k: int = FastAPIQuery(5, ge=1, le=20, description="Number of results"),
    rag_service: RAGService = Depends(get_rag_service)
) -> JSONResponse:
    """
    Simple query endpoint with query string parameters.
    
    Args:
        q: Query question
        use_rag: Whether to use RAG mode
        search_type: Type of search to perform
        top_k: Number of results to return
        rag_service: RAG service dependency
        
    Returns:
        Query response
    """
    try:
        # Create query request
        query_request = QueryRequest(
            question=q,
            use_rag=use_rag,
            search_type=search_type,
            top_k=top_k
        )
        
        # Execute query
        query_response = rag_service.query_documents(query_request)
        
        # Create simple response
        response = {
            "success": True,
            "question": query_response.question,
            "answer": query_response.answer,
            "sources": [
                {
                    "content": source.content[:200] + "..." if len(source.content) > 200 else source.content,
                    "document_name": source.document_name,
                    "score": source.score,
                    "page_number": source.page_number
                }
                for source in query_response.sources
            ],
            "total_sources": query_response.total_sources,
            "processing_time": query_response.processing_time,
            "model_used": query_response.model_used,
            "tokens_used": query_response.tokens_used
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error in simple query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/search/simple",
    summary="Simple search",
    description="Simple search endpoint with query string parameter"
)
async def simple_search(
    q: str = FastAPIQuery(..., description="Search query"),
    search_type: SearchType = FastAPIQuery(SearchType.SEMANTIC, description="Search type"),
    top_k: int = FastAPIQuery(10, ge=1, le=50, description="Number of results"),
    min_score: float = FastAPIQuery(0.0, ge=0.0, le=1.0, description="Minimum relevance score"),
    rag_service: RAGService = Depends(get_rag_service)
) -> JSONResponse:
    """
    Simple search endpoint with query string parameters.
    
    Args:
        q: Search query
        search_type: Type of search to perform
        top_k: Number of results to return
        min_score: Minimum relevance score
        rag_service: RAG service dependency
        
    Returns:
        Search response
    """
    try:
        # Execute search
        sources = rag_service.search_documents_only(
            query=q,
            search_type=search_type,
            top_k=top_k,
            min_score=min_score
        )
        
        # Create simple response
        response = {
            "success": True,
            "query": q,
            "results": [
                {
                    "content": source.content[:300] + "..." if len(source.content) > 300 else source.content,
                    "document_name": source.document_name,
                    "score": source.score,
                    "page_number": source.page_number,
                    "chunk_id": source.chunk_id
                }
                for source in sources
            ],
            "total_results": len(sources),
            "search_type": search_type.value
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error in simple search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/query/test",
    summary="Test RAG pipeline",
    description="Test the complete RAG pipeline with a sample query"
)
async def test_rag_pipeline(
    rag_service: RAGService = Depends(get_rag_service)
) -> JSONResponse:
    """
    Test the complete RAG pipeline.
    
    Args:
        rag_service: RAG service dependency
        
    Returns:
        Test results
    """
    try:
        # Run pipeline test
        test_result = rag_service.test_rag_pipeline()
        
        response = {
            "success": test_result.get('success', False),
            "message": "RAG pipeline test completed",
            "test_results": test_result
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error testing RAG pipeline: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/query/supported-search-types",
    summary="Get supported search types",
    description="Get list of supported search types"
)
async def get_supported_search_types() -> JSONResponse:
    """
    Get supported search types.
    
    Returns:
        List of supported search types
    """
    try:
        search_types = [
            {
                "value": search_type.value,
                "name": search_type.name,
                "description": f"{search_type.value.title()} search"
            }
            for search_type in SearchType
        ]
        
        response = {
            "success": True,
            "message": "Supported search types retrieved",
            "search_types": search_types
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error getting supported search types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
