"""
Document processor for Policy Pilot RAG backend.
Orchestrates the full document processing pipeline.
"""

import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from src.config.settings import settings
from src.core.logging import get_logger
from src.utils.exceptions import DocumentProcessingError, PolicyPilotException
from src.models.document import DocumentStatus, ProcessedDocument, DocumentMetadata, DocumentChunk
from src.services.file_service import FileService
from src.utils.file_handlers import DocumentLoader
from src.utils.text_processing import TextChunker
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService

logger = get_logger(__name__)


class DocumentProcessor:
    """Orchestrates the complete document processing pipeline."""
    
    def __init__(self):
        """Initialize the document processor with all required services."""
        self.file_service = FileService()
        self.document_loader = DocumentLoader()
        self.text_chunker = TextChunker()
        self.embedding_service = EmbeddingService()
        self.search_service = SearchService()
        
        logger.info("DocumentProcessor initialized with all services")
    
    def process_document(self, file_path: Union[str, Path], 
                        filename: str, 
                        document_id: Optional[str] = None) -> ProcessedDocument:
        """
        Process a document through the complete pipeline.
        
        Args:
            file_path: Path to the document file
            filename: Original filename
            document_id: Optional document ID (generated if not provided)
            
        Returns:
            ProcessedDocument with all processing results
            
        Raises:
            DocumentProcessingError: If document processing fails
        """
        start_time = time.time()
        document_id = document_id or self.file_service.generate_document_id(
            Path(file_path).read_bytes(), filename
        )
        
        try:
            logger.info(f"Starting document processing: {filename} (ID: {document_id})")
            
            # Step 1: Load and parse document
            logger.info("Step 1: Loading document")
            document_data = self._load_document(file_path, filename)
            
            # Step 2: Create document metadata
            logger.info("Step 2: Creating document metadata")
            metadata = self._create_document_metadata(document_data, filename, file_path)
            
            # Step 3: Chunk the document
            logger.info("Step 3: Chunking document")
            chunks = self._chunk_document(document_data, document_id, metadata)
            
            # Step 4: Generate embeddings (use streaming for large documents)
            logger.info("Step 4: Generating embeddings")
            if len(chunks) > 1000:  # Use streaming for large documents
                logger.info(f"Using streaming embeddings for large document ({len(chunks)} chunks)")
                chunks_with_embeddings = self._generate_embeddings_streaming(chunks)
            else:
                chunks_with_embeddings = self._generate_embeddings(chunks)
            
            # Step 5: Index documents
            logger.info("Step 5: Indexing documents")
            indexing_result = self._index_documents(chunks_with_embeddings, document_id)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create processed document
            processed_doc = ProcessedDocument(
                document_id=document_id,
                filename=filename,
                status=DocumentStatus.COMPLETED,
                chunks_count=len(chunks_with_embeddings),
                created_at=time.time(),
                completed_at=time.time(),
                processing_time_seconds=processing_time,
                metadata=metadata,
                chunks=chunks_with_embeddings
            )
            
            logger.info(
                f"Document processing completed: {filename} - "
                f"{len(chunks_with_embeddings)} chunks, {processing_time:.2f}s"
            )
            
            return processed_doc
            
        except Exception as e:
            logger.error(f"Document processing failed for {filename}: {e}")
            
            # Create failed document
            processing_time = time.time() - start_time
            failed_doc = ProcessedDocument(
                document_id=document_id,
                filename=filename,
                status=DocumentStatus.FAILED,
                chunks_count=0,
                created_at=time.time(),
                completed_at=time.time(),
                processing_time_seconds=processing_time,
                error_message=str(e),
                metadata=DocumentMetadata(
                    title=filename,
                    file_size=Path(file_path).stat().st_size if Path(file_path).exists() else 0,
                    file_type=self._get_file_type(filename)
                ),
                chunks=[]
            )
            
            return failed_doc
    
    def _load_document(self, file_path: Union[str, Path], filename: str) -> Dict[str, Any]:
        """
        Load and parse document using DocumentLoader.
        
        Args:
            file_path: Path to document file
            filename: Document filename
            
        Returns:
            Document data with text content and metadata
        """
        try:
            file_path = Path(file_path)
            file_type = file_path.suffix.lower()
            
            if not file_path.exists():
                raise DocumentProcessingError(f"File not found: {file_path}")
            
            # Load document
            document_data = self.document_loader.load_document(file_path, file_type)
            
            if not document_data.get('text_content'):
                raise DocumentProcessingError("No text content extracted from document")
            
            logger.info(f"Document loaded: {len(document_data['text_content'])} elements")
            return document_data
            
        except Exception as e:
            logger.error(f"Failed to load document {filename}: {e}")
            raise DocumentProcessingError(f"Failed to load document: {e}")
    
    def _create_document_metadata(self, document_data: Dict[str, Any], 
                                 filename: str, file_path: Union[str, Path]) -> DocumentMetadata:
        """
        Create document metadata from loaded data.
        
        Args:
            document_data: Loaded document data
            filename: Document filename
            file_path: Path to document file
            
        Returns:
            DocumentMetadata object
        """
        try:
            file_path = Path(file_path)
            file_stat = file_path.stat()
            
            # Extract metadata from document data
            doc_metadata = document_data.get('metadata', {})
            
            # Create DocumentMetadata
            metadata = DocumentMetadata(
                title=doc_metadata.get('title') or filename,
                author=doc_metadata.get('author', ''),
                file_size=file_stat.st_size,
                file_type=self._get_file_type(filename),
                total_pages=doc_metadata.get('total_pages'),
                language=doc_metadata.get('language'),
                tags=doc_metadata.get('tags', []),
                description=doc_metadata.get('description', ''),
                custom_metadata={
                    'extraction_method': doc_metadata.get('extraction_method', ''),
                    'file_created': str(doc_metadata.get('created', '')),
                    'file_modified': str(doc_metadata.get('modified', '')),
                    'total_elements': len(document_data.get('text_content', []))
                }
            )
            
            logger.info(f"Document metadata created: {metadata.title}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to create document metadata: {e}")
            raise DocumentProcessingError(f"Failed to create document metadata: {e}")
    
    def _chunk_document(self, document_data: Dict[str, Any], 
                       document_id: str, metadata: DocumentMetadata) -> List[DocumentChunk]:
        """
        Chunk document using TextChunker.
        
        Args:
            document_data: Loaded document data
            document_id: Document identifier
            metadata: Document metadata
            
        Returns:
            List of DocumentChunk objects
        """
        try:
            # Chunk the document
            chunk_data = self.text_chunker.chunk_document(document_data, document_id)
            
            # Convert to DocumentChunk objects
            chunks = []
            for chunk_dict in chunk_data:
                chunk = DocumentChunk(
                    chunk_id=chunk_dict['chunk_id'],
                    content=chunk_dict['content'],
                    metadata=chunk_dict['metadata'],
                    page_number=chunk_dict.get('page_number'),
                    chunk_index=chunk_dict['metadata']['chunk_index'],
                    word_count=chunk_dict['word_count'],
                    char_count=chunk_dict['char_count']
                )
                chunks.append(chunk)
            
            logger.info(f"Document chunked: {len(chunks)} chunks created")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document: {e}")
            raise DocumentProcessingError(f"Failed to chunk document: {e}")
    
    def _generate_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Generate embeddings for document chunks with memory optimization.
        
        Args:
            chunks: List of DocumentChunk objects
            
        Returns:
            List of DocumentChunk objects with embeddings
        """
        try:
            if not chunks:
                return chunks
            
            # Extract text content for embedding
            texts = [chunk.content for chunk in chunks]
            
            # Use optimized batch processing
            embeddings = self.embedding_service.get_embeddings_batch(texts)
            
            # Add embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding.tolist()
            
            logger.info(f"Embeddings generated: {len(embeddings)} vectors")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise DocumentProcessingError(f"Failed to generate embeddings: {e}")
    
    def _generate_embeddings_streaming(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Generate embeddings for document chunks using streaming for large documents.
        
        Args:
            chunks: List of DocumentChunk objects
            
        Returns:
            List of DocumentChunk objects with embeddings
        """
        try:
            if not chunks:
                return chunks
            
            # Extract text content for embedding
            texts = [chunk.content for chunk in chunks]
            
            # Use streaming for large documents
            chunk_index = 0
            for batch_embeddings in self.embedding_service.get_embeddings_streaming(texts):
                # Add embeddings to chunks in this batch
                for embedding in batch_embeddings:
                    if chunk_index < len(chunks):
                        chunks[chunk_index].embedding = embedding.tolist()
                        chunk_index += 1
            
            logger.info(f"Streaming embeddings generated: {len(chunks)} vectors")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to generate streaming embeddings: {e}")
            raise DocumentProcessingError(f"Failed to generate streaming embeddings: {e}")
    
    def _index_documents(self, chunks: List[DocumentChunk], document_id: str) -> Dict[str, Any]:
        """
        Index document chunks in OpenSearch.
        
        Args:
            chunks: List of DocumentChunk objects with embeddings
            document_id: Document identifier
            
        Returns:
            Indexing results
        """
        try:
            if not chunks:
                return {'success': True, 'indexed_count': 0, 'failed_count': 0}
            
            # Prepare documents for indexing
            index_docs = []
            for chunk in chunks:
                doc = {
                    'chunk_id': chunk.chunk_id,
                    'document_id': document_id,
                    'content': chunk.content,
                    'embedding': chunk.embedding,
                    'metadata': chunk.metadata,
                    'document_title': '',  # Will be filled from metadata
                    'document_filename': '',  # Will be filled from metadata
                    'created_at': time.time(),
                    'updated_at': time.time()
                }
                index_docs.append(doc)
            
            # Index documents
            result = self.search_service.index_documents(index_docs)
            
            if result['success']:
                logger.info(f"Documents indexed: {result['indexed_count']} chunks")
            else:
                logger.warning(f"Indexing completed with errors: {result['failed_count']} failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            raise DocumentProcessingError(f"Failed to index documents: {e}")
    
    def _get_file_type(self, filename: str) -> str:
        """
        Get MIME type for filename.
        
        Args:
            filename: Document filename
            
        Returns:
            MIME type string
        """
        extension = Path(filename).suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.rtf': 'application/rtf'
        }
        return mime_types.get(extension, 'application/octet-stream')
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        try:
            # Get service health
            embedding_health = self.embedding_service.health_check()
            search_health = self.search_service.health_check()
            
            # Get search stats
            search_stats = self.search_service.get_document_stats()
            
            return {
                'embedding_service': embedding_health,
                'search_service': search_health,
                'document_stats': search_stats,
                'chunk_size': self.text_chunker.chunk_size,
                'chunk_overlap': self.text_chunker.chunk_overlap
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing stats: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all processing services.
        
        Returns:
            Health check results
        """
        try:
            # Check individual services
            embedding_health = self.embedding_service.health_check()
            search_health = self.search_service.health_check()
            
            # Determine overall status
            overall_status = 'healthy'
            if embedding_health['status'] != 'healthy' or search_health['status'] != 'healthy':
                overall_status = 'degraded'
            if embedding_health['status'] == 'unhealthy' and search_health['status'] == 'unhealthy':
                overall_status = 'unhealthy'
            
            return {
                'status': overall_status,
                'embedding_service': embedding_health,
                'search_service': search_health,
                'services_available': {
                    'embedding': embedding_health['status'] == 'healthy',
                    'search': search_health['status'] == 'healthy'
                }
            }
            
        except Exception as e:
            logger.error(f"Document processor health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
