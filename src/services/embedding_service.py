"""
Embedding service for Policy Pilot RAG backend.
Handles text embedding generation using sentence-transformers with optimizations.
"""

import gc
import time
import numpy as np
from typing import List, Dict, Any, Optional, Union, Iterator
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

from src.config.settings import settings
from src.core.logging import get_logger
from src.utils.exceptions import EmbeddingServiceError, ConfigurationError

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating and managing text embeddings with optimizations."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name or settings.embedding_model
        self.model: Optional[SentenceTransformer] = None
        self.embedding_dimension: Optional[int] = None
        self.max_seq_length: int = 512  # Default for most models
        self._model_lock = threading.Lock()
        self._batch_size = 32
        self._max_workers = min(4, psutil.cpu_count())
        self._memory_threshold = 0.8  # 80% memory usage threshold
        
        logger.info(f"EmbeddingService initialized with model: {self.model_name}")
        logger.info(f"Batch processing: batch_size={self._batch_size}, max_workers={self._max_workers}")
    
    def load_model(self) -> None:
        """
        Load the sentence transformer model with thread safety.
        
        Raises:
            EmbeddingServiceError: If model loading fails
        """
        with self._model_lock:
            try:
                if self.model is not None:
                    logger.info("Model already loaded")
                    return
                
                logger.info(f"Loading sentence transformer model: {self.model_name}")
                start_time = time.time()
                
                # Load model with optimizations
                self.model = SentenceTransformer(
                    self.model_name,
                    device='cpu',  # Use CPU for better memory management
                    cache_folder=None  # Use default cache
                )
                
                # Get model information
                self.embedding_dimension = self.model.get_sentence_embedding_dimension()
                self.max_seq_length = getattr(self.model, 'max_seq_length', 512)
                
                load_time = time.time() - start_time
                logger.info(
                    f"Model loaded successfully in {load_time:.2f}s: "
                    f"dimension={self.embedding_dimension}, "
                    f"max_seq_length={self.max_seq_length}"
                )
                
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise EmbeddingServiceError(f"Failed to load embedding model '{self.model_name}': {e}")
    
    def get_embedding(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            normalize: Whether to normalize the embedding vector
            
        Returns:
            Embedding vector as numpy array
            
        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        try:
            if self.model is None:
                self.load_model()
            
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            if not processed_text.strip():
                raise EmbeddingServiceError("Empty text after preprocessing")
            
            # Generate embedding
            embedding = self.model.encode(
                processed_text,
                normalize_embeddings=normalize,
                convert_to_numpy=True
            )
            
            logger.debug(f"Generated embedding for text: {len(processed_text)} chars")
            return embedding
            
        except EmbeddingServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise EmbeddingServiceError(f"Failed to generate embedding: {e}")
    
    def get_embeddings_batch(self, texts: List[str], normalize: bool = True, 
                            batch_size: Optional[int] = None) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently with memory optimization.
        
        Args:
            texts: List of texts to embed
            normalize: Whether to normalize the embedding vectors
            batch_size: Batch size for processing (uses optimized default if None)
            
        Returns:
            List of embedding vectors as numpy arrays
            
        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        try:
            if self.model is None:
                self.load_model()
            
            if not texts:
                return []
            
            # Use optimized batch size
            if batch_size is None:
                batch_size = self._get_optimal_batch_size(len(texts))
            
            # Preprocess all texts
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # Filter out empty texts
            valid_texts = [text for text in processed_texts if text.strip()]
            if not valid_texts:
                raise EmbeddingServiceError("No valid texts after preprocessing")
            
            logger.info(f"Generating embeddings for {len(valid_texts)} texts (batch_size={batch_size})")
            start_time = time.time()
            
            # Check memory before processing
            self._check_memory_usage()
            
            # Generate embeddings in optimized batches
            embeddings = self._generate_embeddings_optimized(
                valid_texts, normalize, batch_size
            )
            
            # Convert to list of arrays
            embedding_list = [emb for emb in embeddings]
            
            processing_time = time.time() - start_time
            logger.info(
                f"Generated {len(embedding_list)} embeddings successfully in {processing_time:.2f}s "
                f"({len(embedding_list)/processing_time:.1f} embeddings/sec)"
            )
            
            # Force garbage collection
            gc.collect()
            
            return embedding_list
            
        except EmbeddingServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise EmbeddingServiceError(f"Failed to generate batch embeddings: {e}")
    
    def _generate_embeddings_optimized(self, texts: List[str], normalize: bool, 
                                     batch_size: int) -> np.ndarray:
        """
        Generate embeddings with memory optimization and progress tracking.
        
        Args:
            texts: List of texts to embed
            normalize: Whether to normalize embeddings
            batch_size: Batch size for processing
            
        Returns:
            Numpy array of embeddings
        """
        try:
            # Process in chunks to manage memory
            all_embeddings = []
            total_batches = (len(texts) + batch_size - 1) // batch_size
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                logger.debug(f"Processing batch {batch_num}/{total_batches} ({len(batch_texts)} texts)")
                
                # Generate embeddings for this batch
                batch_embeddings = self.model.encode(
                    batch_texts,
                    normalize_embeddings=normalize,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    batch_size=min(batch_size, len(batch_texts))
                )
                
                all_embeddings.append(batch_embeddings)
                
                # Check memory usage after each batch
                if batch_num % 5 == 0:  # Check every 5 batches
                    self._check_memory_usage()
            
            # Concatenate all embeddings
            if len(all_embeddings) == 1:
                return all_embeddings[0]
            else:
                return np.vstack(all_embeddings)
                
        except Exception as e:
            logger.error(f"Failed to generate optimized embeddings: {e}")
            raise EmbeddingServiceError(f"Failed to generate optimized embeddings: {e}")
    
    def _get_optimal_batch_size(self, num_texts: int) -> int:
        """
        Calculate optimal batch size based on available memory and text count.
        
        Args:
            num_texts: Number of texts to process
            
        Returns:
            Optimal batch size
        """
        try:
            # Get available memory
            memory = psutil.virtual_memory()
            available_memory_gb = memory.available / (1024**3)
            
            # Base batch size on available memory
            if available_memory_gb > 8:
                base_batch_size = 64
            elif available_memory_gb > 4:
                base_batch_size = 32
            elif available_memory_gb > 2:
                base_batch_size = 16
            else:
                base_batch_size = 8
            
            # Adjust based on number of texts
            if num_texts < 100:
                return min(base_batch_size, num_texts)
            elif num_texts < 1000:
                return min(base_batch_size * 2, num_texts)
            else:
                return min(base_batch_size * 4, num_texts)
                
        except Exception as e:
            logger.warning(f"Failed to calculate optimal batch size: {e}")
            return self._batch_size
    
    def _check_memory_usage(self) -> None:
        """
        Check memory usage and trigger garbage collection if needed.
        
        Raises:
            EmbeddingServiceError: If memory usage is too high
        """
        try:
            memory = psutil.virtual_memory()
            memory_usage = memory.percent / 100
            
            if memory_usage > self._memory_threshold:
                logger.warning(f"High memory usage: {memory.percent:.1f}%")
                gc.collect()
                
                # Check again after garbage collection
                memory = psutil.virtual_memory()
                memory_usage = memory.percent / 100
                
                if memory_usage > self._memory_threshold:
                    raise EmbeddingServiceError(
                        f"Memory usage too high: {memory.percent:.1f}%. "
                        f"Consider reducing batch size or processing fewer texts at once."
                    )
                    
        except Exception as e:
            logger.warning(f"Failed to check memory usage: {e}")
    
    def get_embeddings_streaming(self, texts: List[str], normalize: bool = True, 
                                batch_size: Optional[int] = None) -> Iterator[np.ndarray]:
        """
        Generate embeddings in a streaming fashion for very large datasets.
        
        Args:
            texts: List of texts to embed
            normalize: Whether to normalize the embedding vectors
            batch_size: Batch size for processing
            
        Yields:
            Numpy arrays of embeddings in batches
        """
        try:
            if self.model is None:
                self.load_model()
            
            if not texts:
                return
            
            if batch_size is None:
                batch_size = self._get_optimal_batch_size(len(texts))
            
            # Preprocess all texts
            processed_texts = [self._preprocess_text(text) for text in texts]
            valid_texts = [text for text in processed_texts if text.strip()]
            
            if not valid_texts:
                raise EmbeddingServiceError("No valid texts after preprocessing")
            
            logger.info(f"Streaming embeddings for {len(valid_texts)} texts (batch_size={batch_size})")
            
            # Process in batches and yield results
            for i in range(0, len(valid_texts), batch_size):
                batch_texts = valid_texts[i:i + batch_size]
                
                # Generate embeddings for this batch
                batch_embeddings = self.model.encode(
                    batch_texts,
                    normalize_embeddings=normalize,
                    convert_to_numpy=True,
                    show_progress_bar=False
                )
                
                yield batch_embeddings
                
                # Check memory after each batch
                self._check_memory_usage()
                
        except Exception as e:
            logger.error(f"Failed to generate streaming embeddings: {e}")
            raise EmbeddingServiceError(f"Failed to generate streaming embeddings: {e}")
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text before embedding generation.
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text
        """
        try:
            if not text or not isinstance(text, str):
                return ""
            
            # Basic cleaning
            processed = text.strip()
            
            # Truncate if too long
            if len(processed) > self.max_seq_length * 4:  # Rough character limit
                processed = processed[:self.max_seq_length * 4]
                logger.debug(f"Truncated text from {len(text)} to {len(processed)} characters")
            
            # Remove excessive whitespace
            processed = ' '.join(processed.split())
            
            return processed
            
        except Exception as e:
            logger.warning(f"Text preprocessing failed: {e}")
            return text if isinstance(text, str) else ""
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
            
        Raises:
            EmbeddingServiceError: If similarity calculation fails
        """
        try:
            # Ensure embeddings are 2D arrays
            if embedding1.ndim == 1:
                embedding1 = embedding1.reshape(1, -1)
            if embedding2.ndim == 1:
                embedding2 = embedding2.reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(embedding1, embedding2)[0][0]
            
            # Ensure similarity is between 0 and 1
            similarity = max(0.0, min(1.0, similarity))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            raise EmbeddingServiceError(f"Failed to calculate similarity: {e}")
    
    def find_most_similar(self, query_embedding: np.ndarray, 
                         candidate_embeddings: List[np.ndarray], 
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find most similar embeddings to a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            top_k: Number of top results to return
            
        Returns:
            List of similarity results with scores and indices
        """
        try:
            if not candidate_embeddings:
                return []
            
            # Calculate similarities
            similarities = []
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.calculate_similarity(query_embedding, candidate)
                similarities.append({
                    'index': i,
                    'similarity': similarity
                })
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Return top_k results
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to find most similar embeddings: {e}")
            raise EmbeddingServiceError(f"Failed to find most similar embeddings: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        try:
            if self.model is None:
                return {
                    'model_name': self.model_name,
                    'loaded': False,
                    'error': 'Model not loaded'
                }
            
            return {
                'model_name': self.model_name,
                'loaded': True,
                'embedding_dimension': self.embedding_dimension,
                'max_seq_length': self.max_seq_length,
                'model_type': type(self.model).__name__
            }
            
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {
                'model_name': self.model_name,
                'loaded': False,
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the embedding service.
        
        Returns:
            Health check results
        """
        try:
            # Check if model is loaded
            if self.model is None:
                return {
                    'status': 'unhealthy',
                    'error': 'Model not loaded',
                    'model_name': self.model_name
                }
            
            # Test embedding generation
            test_text = "This is a test for embedding generation."
            test_embedding = self.get_embedding(test_text)
            
            if test_embedding is None or len(test_embedding) == 0:
                return {
                    'status': 'unhealthy',
                    'error': 'Failed to generate test embedding',
                    'model_name': self.model_name
                }
            
            return {
                'status': 'healthy',
                'model_name': self.model_name,
                'embedding_dimension': self.embedding_dimension,
                'test_embedding_length': len(test_embedding)
            }
            
        except Exception as e:
            logger.error(f"Embedding service health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'model_name': self.model_name
            }
    
    def __del__(self):
        """Cleanup when service is destroyed."""
        try:
            if hasattr(self, 'model') and self.model is not None:
                # Clear model from memory
                del self.model
                self.model = None
        except Exception as e:
            logger.warning(f"Error during embedding service cleanup: {e}")
