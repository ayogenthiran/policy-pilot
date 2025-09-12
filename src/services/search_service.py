"""
Search service for Policy Pilot RAG backend.
Handles OpenSearch operations for document indexing and searching.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import numpy as np
from opensearchpy import OpenSearch
from opensearchpy.exceptions import OpenSearchException, NotFoundError

from src.config.database import opensearch_connection
from src.config.settings import settings
from src.core.logging import get_logger
from src.utils.exceptions import SearchServiceError, OpenSearchError
from src.models.document import DocumentSearchResult
from src.models.query import SearchType, Source
from src.services.cache_service import cache_service

logger = get_logger(__name__)


class SearchService:
    """Service for OpenSearch operations and document searching."""
    
    def __init__(self):
        """Initialize the search service."""
        self.client: Optional[OpenSearch] = None
        self.index_name = settings.opensearch_index
        self.embedding_dimension = 768  # Default for all-mpnet-base-v2
        
        logger.info(f"SearchService initialized for index: {self.index_name}")
    
    def _get_client(self) -> OpenSearch:
        """Get OpenSearch client instance."""
        if self.client is None:
            self.client = opensearch_connection.get_client()
        return self.client
    
    def ensure_index_exists(self) -> bool:
        """
        Ensure the OpenSearch index exists.
        
        Returns:
            True if index exists or was created successfully
            
        Raises:
            SearchServiceError: If index creation fails
        """
        try:
            client = self._get_client()
            
            if client.indices.exists(index=self.index_name):
                logger.info(f"Index {self.index_name} already exists")
                return True
            
            return self.create_index()
            
        except Exception as e:
            logger.error(f"Failed to ensure index exists: {e}")
            raise SearchServiceError(f"Failed to ensure index exists: {e}")
    
    def create_index(self) -> bool:
        """
        Create the OpenSearch index with proper mappings.
        
        Returns:
            True if index was created successfully
            
        Raises:
            SearchServiceError: If index creation fails
        """
        try:
            client = self._get_client()
            
            # Index mapping configuration
            index_mapping = {
                "settings": {
                    "index": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "knn": True,
                        "knn.algo_param.ef_construction": 128,
                        "knn.algo_param.m": 24
                    },
                    "analysis": {
                        "analyzer": {
                            "custom_text_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "stop", "snowball"]
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "chunk_id": {
                            "type": "keyword"
                        },
                        "document_id": {
                            "type": "keyword"
                        },
                        "content": {
                            "type": "text",
                            "analyzer": "custom_text_analyzer",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": self.embedding_dimension,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib",
                                "parameters": {
                                    "ef_construction": 128,
                                    "m": 24
                                }
                            }
                        },
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "page_number": {"type": "integer"},
                                "chunk_index": {"type": "integer"},
                                "word_count": {"type": "integer"},
                                "char_count": {"type": "integer"},
                                "file_type": {"type": "keyword"},
                                "extraction_method": {"type": "keyword"}
                            }
                        },
                        "document_metadata": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "text", "analyzer": "custom_text_analyzer"},
                                "author": {"type": "keyword"},
                                "file_type": {"type": "keyword"},
                                "file_size": {"type": "integer"},
                                "total_pages": {"type": "integer"},
                                "created_at": {"type": "date"},
                                "updated_at": {"type": "date"},
                                "tags": {"type": "keyword"}
                            }
                        },
                        "document_title": {
                            "type": "text",
                            "analyzer": "custom_text_analyzer"
                        },
                        "document_filename": {
                            "type": "keyword"
                        },
                        "created_at": {
                            "type": "date"
                        },
                        "updated_at": {
                            "type": "date"
                        }
                    }
                }
            }
            
            # Create index
            response = client.indices.create(
                index=self.index_name,
                body=index_mapping
            )
            
            logger.info(f"Index {self.index_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            raise SearchServiceError(f"Failed to create OpenSearch index: {e}")
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk index documents with embeddings.
        
        Args:
            documents: List of document dictionaries with embeddings
            
        Returns:
            Indexing results with success/failure counts
            
        Raises:
            SearchServiceError: If indexing fails
        """
        try:
            client = self._get_client()
            
            # Ensure index exists
            self.ensure_index_exists()
            
            # Prepare bulk indexing data
            bulk_data = []
            for doc in documents:
                # Index action
                bulk_data.append({
                    "index": {
                        "_index": self.index_name,
                        "_id": doc.get('chunk_id')
                    }
                })
                
                # Document data
                bulk_data.append(doc)
            
            if not bulk_data:
                return {
                    'success': True,
                    'indexed_count': 0,
                    'failed_count': 0,
                    'errors': []
                }
            
            # Perform bulk indexing
            response = client.bulk(body=bulk_data)
            
            # Process results
            indexed_count = 0
            failed_count = 0
            errors = []
            
            for item in response['items']:
                if 'index' in item:
                    if item['index']['status'] in [200, 201]:
                        indexed_count += 1
                    else:
                        failed_count += 1
                        errors.append(item['index'].get('error', 'Unknown error'))
            
            result = {
                'success': failed_count == 0,
                'indexed_count': indexed_count,
                'failed_count': failed_count,
                'errors': errors
            }
            
            logger.info(f"Bulk indexing completed: {indexed_count} indexed, {failed_count} failed")
            return result
            
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            raise SearchServiceError(f"Failed to index documents: {e}")
    
    def hybrid_search(self, query: str, query_embedding: np.ndarray, 
                     search_type: SearchType = SearchType.HYBRID,
                     top_k: int = 10, min_score: float = 0.0) -> List[DocumentSearchResult]:
        """
        Perform hybrid search combining BM25 and vector similarity with caching.
        
        Args:
            query: Search query text
            query_embedding: Query embedding vector
            search_type: Type of search to perform
            top_k: Number of results to return
            min_score: Minimum relevance score threshold
            
        Returns:
            List of search results
            
        Raises:
            SearchServiceError: If search fails
        """
        try:
            # Generate cache key
            cache_key = cache_service.generate_key(
                'search', query, search_type.value, top_k, min_score,
                embedding_hash=hash(query_embedding.tobytes())
            )
            
            # Try to get from cache
            cached_results = cache_service.get(cache_key)
            if cached_results is not None:
                logger.debug(f"Search cache hit for query: {query[:50]}...")
                return cached_results
            
            # Perform search
            client = self._get_client()
            
            if search_type == SearchType.SEMANTIC:
                results = self._semantic_search(query_embedding, top_k, min_score)
            elif search_type == SearchType.KEYWORD:
                results = self._keyword_search(query, top_k, min_score)
            else:  # HYBRID
                results = self._hybrid_search_impl(query, query_embedding, top_k, min_score)
            
            # Cache results for 5 minutes
            cache_service.set(cache_key, results, ttl=300)
            logger.debug(f"Search results cached for query: {query[:50]}...")
            
            return results
                
        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {e}")
            raise SearchServiceError(f"Failed to perform search: {e}")
    
    def _semantic_search(self, query_embedding: np.ndarray, top_k: int, min_score: float) -> List[DocumentSearchResult]:
        """Perform semantic search using vector similarity."""
        try:
            client = self._get_client()
            
            search_body = {
                "size": top_k,
                "min_score": min_score,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_embedding.tolist(),
                            "k": top_k
                        }
                    }
                },
                "_source": [
                    "chunk_id", "document_id", "content", "metadata", 
                    "document_title", "document_filename"
                ]
            }
            
            response = client.search(index=self.index_name, body=search_body)
            return self._format_results(response['hits']['hits'])
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise SearchServiceError(f"Semantic search failed: {e}")
    
    def _keyword_search(self, query: str, top_k: int, min_score: float) -> List[DocumentSearchResult]:
        """Perform keyword search using BM25."""
        try:
            client = self._get_client()
            
            search_body = {
                "size": top_k,
                "min_score": min_score,
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["content^2", "document_title^1.5", "document_metadata.title^1.2"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "_source": [
                    "chunk_id", "document_id", "content", "metadata", 
                    "document_title", "document_filename"
                ]
            }
            
            response = client.search(index=self.index_name, body=search_body)
            return self._format_results(response['hits']['hits'])
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            raise SearchServiceError(f"Keyword search failed: {e}")
    
    def _hybrid_search_impl(self, query: str, query_embedding: np.ndarray, 
                           top_k: int, min_score: float) -> List[DocumentSearchResult]:
        """Perform hybrid search combining BM25 and vector similarity."""
        try:
            client = self._get_client()
            
            search_body = {
                "size": top_k,
                "min_score": min_score,
                "query": {
                    "bool": {
                        "should": [
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": query_embedding.tolist(),
                                        "k": top_k,
                                        "boost": 0.7
                                    }
                                }
                            },
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["content^2", "document_title^1.5"],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO",
                                    "boost": 0.3
                                }
                            }
                        ]
                    }
                },
                "_source": [
                    "chunk_id", "document_id", "content", "metadata", 
                    "document_title", "document_filename"
                ]
            }
            
            response = client.search(index=self.index_name, body=search_body)
            return self._format_results(response['hits']['hits'])
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise SearchServiceError(f"Hybrid search failed: {e}")
    
    def _format_results(self, hits: List[Dict[str, Any]]) -> List[DocumentSearchResult]:
        """
        Format search results into standardized format.
        
        Args:
            hits: Raw search hits from OpenSearch
            
        Returns:
            List of formatted search results
        """
        try:
            results = []
            
            for hit in hits:
                source = hit['_source']
                score = hit['_score']
                
                # Extract metadata
                metadata = source.get('metadata', {})
                page_number = metadata.get('page_number')
                
                result = DocumentSearchResult(
                    chunk_id=source.get('chunk_id', ''),
                    document_id=source.get('document_id', ''),
                    content=source.get('content', ''),
                    score=float(score),
                    page_number=page_number,
                    metadata=metadata,
                    document_title=source.get('document_title', ''),
                    document_filename=source.get('document_filename', '')
                )
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to format search results: {e}")
            raise SearchServiceError(f"Failed to format search results: {e}")
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            SearchServiceError: If deletion fails
        """
        try:
            client = self._get_client()
            
            # Delete by query
            delete_body = {
                "query": {
                    "term": {
                        "document_id": document_id
                    }
                }
            }
            
            response = client.delete_by_query(
                index=self.index_name,
                body=delete_body
            )
            
            deleted_count = response.get('deleted', 0)
            logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise SearchServiceError(f"Failed to delete document: {e}")
    
    def get_document_stats(self) -> Dict[str, Any]:
        """
        Get statistics about indexed documents.
        
        Returns:
            Dictionary with document statistics
        """
        try:
            client = self._get_client()
            
            # Get index stats
            stats = client.indices.stats(index=self.index_name)
            index_stats = stats['indices'][self.index_name]
            
            # Get document count
            count_response = client.count(index=self.index_name)
            doc_count = count_response['count']
            
            return {
                'total_documents': doc_count,
                'index_size_bytes': index_stats['total']['store']['size_in_bytes'],
                'index_size_mb': round(index_stats['total']['store']['size_in_bytes'] / (1024 * 1024), 2),
                'index_name': self.index_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get document stats: {e}")
            return {
                'total_documents': 0,
                'index_size_bytes': 0,
                'index_size_mb': 0,
                'index_name': self.index_name,
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the search service.
        
        Returns:
            Health check results
        """
        try:
            # Check OpenSearch connection
            opensearch_health = opensearch_connection.health_check()
            
            if opensearch_health['status'] != 'healthy':
                return {
                    'status': 'unhealthy',
                    'error': 'OpenSearch connection unhealthy',
                    'opensearch_health': opensearch_health
                }
            
            # Check index exists
            client = self._get_client()
            index_exists = client.indices.exists(index=self.index_name)
            
            if not index_exists:
                return {
                    'status': 'degraded',
                    'error': 'Index does not exist',
                    'index_name': self.index_name
                }
            
            # Get basic stats
            stats = self.get_document_stats()
            
            return {
                'status': 'healthy',
                'index_name': self.index_name,
                'index_exists': index_exists,
                'document_count': stats['total_documents'],
                'opensearch_health': opensearch_health
            }
            
        except Exception as e:
            logger.error(f"Search service health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'index_name': self.index_name
            }
