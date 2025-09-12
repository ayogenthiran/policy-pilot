"""
RAG service for Policy Pilot RAG backend.
Main orchestration service for the complete RAG workflow.
"""

import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from src.config.settings import settings
from src.core.logging import get_logger
from src.utils.exceptions import PolicyPilotException, DocumentProcessingError, SearchServiceError, GPTServiceError
from src.models.document import ProcessedDocument, DocumentStatus
from src.models.query import QueryRequest, QueryResponse, SearchType, Source
from src.services.document_processor import DocumentProcessor
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService
from src.services.gpt_service import GPTService
from src.config.database import opensearch_connection

logger = get_logger(__name__)


class RAGService:
    """Main RAG orchestration service."""
    
    def __init__(self):
        """Initialize the RAG service with all required components."""
        self.document_processor = DocumentProcessor()
        self.embedding_service = EmbeddingService()
        self.search_service = SearchService()
        self.gpt_service = GPTService()
        
        logger.info("RAGService initialized with all components")
    
    def process_document(self, file_path: Union[str, Path], 
                        filename: str, 
                        document_id: Optional[str] = None) -> ProcessedDocument:
        """
        Process a document through the complete RAG pipeline.
        
        Args:
            file_path: Path to the document file
            filename: Original filename
            document_id: Optional document ID (generated if not provided)
            
        Returns:
            ProcessedDocument with processing results
        """
        try:
            logger.info(f"RAG processing document: {filename}")
            return self.document_processor.process_document(file_path, filename, document_id)
            
        except Exception as e:
            logger.error(f"RAG document processing failed for {filename}: {e}")
            raise DocumentProcessingError(f"RAG document processing failed: {e}")
    
    def query_documents(self, query_request: QueryRequest) -> QueryResponse:
        """
        Execute the complete RAG query pipeline.
        
        Args:
            query_request: Query request with parameters
            
        Returns:
            QueryResponse with generated answer and sources
        """
        try:
            start_time = time.time()
            logger.info(f"RAG query: {query_request.question[:100]}...")
            
            # Step 1: Generate query embedding
            query_embedding = None
            if query_request.use_rag:
                query_embedding = self._generate_query_embedding(query_request.question)
            
            # Step 2: Search for relevant documents
            sources = []
            if query_request.use_rag and query_embedding is not None:
                sources = self._search_documents(query_request, query_embedding)
            
            # Step 3: Generate answer using GPT
            query_response = self._generate_answer(query_request, sources)
            
            # Calculate total processing time
            total_time = time.time() - start_time
            query_response.processing_time = total_time
            
            logger.info(
                f"RAG query completed: {len(sources)} sources, "
                f"{query_response.tokens_used or 0} tokens, {total_time:.2f}s"
            )
            
            return query_response
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            # Return error response
            return QueryResponse(
                question=query_request.question,
                answer=f"I apologize, but I encountered an error while processing your query: {str(e)}",
                sources=[],
                search_type=query_request.search_type,
                total_sources=0,
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    def _generate_query_embedding(self, question: str) -> Optional[List[float]]:
        """
        Generate embedding for the query question.
        
        Args:
            question: Query question text
            
        Returns:
            Query embedding vector or None if failed
        """
        try:
            embedding = self.embedding_service.get_embedding(question)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return None
    
    def _search_documents(self, query_request: QueryRequest, 
                         query_embedding: List[float]) -> List[Source]:
        """
        Search for relevant documents using the query embedding.
        
        Args:
            query_request: Query request with search parameters
            query_embedding: Query embedding vector
            
        Returns:
            List of relevant document sources
        """
        try:
            # Convert to numpy array for search
            import numpy as np
            query_embedding_array = np.array(query_embedding)
            
            # Perform search
            search_results = self.search_service.hybrid_search(
                query=query_request.question,
                query_embedding=query_embedding_array,
                search_type=query_request.search_type,
                top_k=query_request.top_k,
                min_score=query_request.min_score
            )
            
            # Convert to Source objects
            sources = []
            for result in search_results:
                source = Source(
                    content=result.content,
                    document_name=result.document_title or result.document_filename,
                    score=result.score,
                    chunk_id=result.chunk_id,
                    page_number=result.page_number,
                    metadata=result.metadata,
                    document_id=result.document_id,
                    document_title=result.document_title
                )
                sources.append(source)
            
            logger.info(f"Found {len(sources)} relevant sources")
            return sources
            
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return []
    
    def _generate_answer(self, query_request: QueryRequest, 
                        sources: List[Source]) -> QueryResponse:
        """
        Generate answer using GPT service.
        
        Args:
            query_request: Query request with parameters
            sources: Retrieved document sources
            
        Returns:
            QueryResponse with generated answer
        """
        try:
            # Generate answer using GPT service
            query_response = self.gpt_service.generate_answer(
                query_request=query_request,
                sources=sources
            )
            
            return query_response
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            raise GPTServiceError(f"Failed to generate answer: {e}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Check health of all RAG service components.
        
        Returns:
            Comprehensive health check results
        """
        try:
            # Check individual services
            embedding_health = self.embedding_service.health_check()
            search_health = self.search_service.health_check()
            gpt_health = self.gpt_service.health_check()
            opensearch_health = opensearch_connection.health_check()
            
            # Check document processor
            processor_health = self.document_processor.health_check()
            
            # Determine overall status
            service_statuses = [
                embedding_health['status'],
                search_health['status'],
                gpt_health['status'],
                opensearch_health['status']
            ]
            
            if all(status == 'healthy' for status in service_statuses):
                overall_status = 'healthy'
            elif any(status == 'unhealthy' for status in service_statuses):
                overall_status = 'unhealthy'
            else:
                overall_status = 'degraded'
            
            # Get system statistics
            search_stats = self.search_service.get_document_stats()
            embedding_info = self.embedding_service.get_model_info()
            gpt_info = self.gpt_service.get_model_info()
            
            return {
                'status': overall_status,
                'timestamp': time.time(),
                'services': {
                    'embedding_service': embedding_health,
                    'search_service': search_health,
                    'gpt_service': gpt_health,
                    'opensearch_connection': opensearch_health,
                    'document_processor': processor_health
                },
                'statistics': {
                    'total_documents': search_stats.get('total_documents', 0),
                    'index_size_mb': search_stats.get('index_size_mb', 0),
                    'embedding_model': embedding_info.get('model_name', 'unknown'),
                    'gpt_model': gpt_info.get('model_name', 'unknown')
                },
                'configuration': {
                    'chunk_size': settings.chunk_size,
                    'chunk_overlap': settings.chunk_overlap,
                    'max_file_size': settings.max_file_size,
                    'opensearch_url': settings.opensearch_url,
                    'opensearch_index': settings.opensearch_index
                }
            }
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }
    
    def get_document_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive document statistics.
        
        Returns:
            Dictionary with document statistics
        """
        try:
            # Get search service stats
            search_stats = self.search_service.get_document_stats()
            
            # Get processing stats
            processing_stats = self.document_processor.get_processing_stats()
            
            return {
                'documents': {
                    'total_documents': search_stats.get('total_documents', 0),
                    'index_size_bytes': search_stats.get('index_size_bytes', 0),
                    'index_size_mb': search_stats.get('index_size_mb', 0)
                },
                'processing': processing_stats,
                'index_name': search_stats.get('index_name', settings.opensearch_index),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to get document statistics: {e}")
            return {
                'error': str(e),
                'timestamp': time.time()
            }
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete a document and all its chunks from the system.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            Deletion results
        """
        try:
            # Delete from search index
            success = self.search_service.delete_document(document_id)
            
            if success:
                logger.info(f"Document {document_id} deleted successfully")
                return {
                    'success': True,
                    'document_id': document_id,
                    'message': 'Document deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'document_id': document_id,
                    'message': 'Failed to delete document'
                }
                
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return {
                'success': False,
                'document_id': document_id,
                'error': str(e)
            }
    
    def search_documents_only(self, query: str, search_type: SearchType = SearchType.SEMANTIC,
                             top_k: int = 10, min_score: float = 0.0) -> List[Source]:
        """
        Search documents without generating an answer.
        
        Args:
            query: Search query
            search_type: Type of search to perform
            top_k: Number of results to return
            min_score: Minimum relevance score
            
        Returns:
            List of search results
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.get_embedding(query)
            
            # Search documents
            search_results = self.search_service.hybrid_search(
                query=query,
                query_embedding=query_embedding,
                search_type=search_type,
                top_k=top_k,
                min_score=min_score
            )
            
            # Convert to Source objects
            sources = []
            for result in search_results:
                source = Source(
                    content=result.content,
                    document_name=result.document_title or result.document_filename,
                    score=result.score,
                    chunk_id=result.chunk_id,
                    page_number=result.page_number,
                    metadata=result.metadata,
                    document_id=result.document_id,
                    document_title=result.document_title
                )
                sources.append(source)
            
            return sources
            
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return []
    
    def test_rag_pipeline(self) -> Dict[str, Any]:
        """
        Test the complete RAG pipeline with a sample query.
        
        Returns:
            Test results
        """
        try:
            # Create test query
            test_query = QueryRequest(
                question="What is the main purpose of this system?",
                use_rag=True,
                search_type=SearchType.SEMANTIC,
                top_k=3
            )
            
            # Execute RAG pipeline
            start_time = time.time()
            response = self.query_documents(test_query)
            total_time = time.time() - start_time
            
            return {
                'success': True,
                'test_query': test_query.question,
                'response_length': len(response.answer),
                'sources_found': len(response.sources),
                'processing_time': total_time,
                'tokens_used': response.tokens_used,
                'error': response.error
            }
            
        except Exception as e:
            logger.error(f"RAG pipeline test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_query': "What is the main purpose of this system?"
            }
