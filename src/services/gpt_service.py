"""
GPT service for Policy Pilot RAG backend.
Handles OpenAI GPT-4o-mini integration for answer generation.
"""

import time
from typing import Dict, List, Any, Optional, Union
from openai import OpenAI, RateLimitError, APIError, APITimeoutError
from openai.types.chat import ChatCompletion

from src.config.settings import settings
from src.core.logging import get_logger
from src.utils.exceptions import GPTServiceError, ConfigurationError
from src.models.query import QueryRequest, QueryResponse, Source
from src.services.cache_service import cache_service

logger = get_logger(__name__)


class GPTService:
    """Service for OpenAI GPT-4o-mini integration."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the GPT service.
        
        Args:
            api_key: OpenAI API key (uses settings if not provided)
            model: GPT model name (uses settings if not provided)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.client: Optional[OpenAI] = None
        
        if not self.api_key:
            raise ConfigurationError("OpenAI API key not provided")
        
        logger.info(f"GPTService initialized with model: {self.model}")
    
    def _get_client(self) -> OpenAI:
        """Get OpenAI client instance."""
        if self.client is None:
            self.client = OpenAI(api_key=self.api_key)
        return self.client
    
    def check_connection(self) -> Dict[str, Any]:
        """
        Test OpenAI API connectivity.
        
        Returns:
            Connection test results
        """
        try:
            client = self._get_client()
            
            # Test with a simple completion
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Hello, this is a connection test."}
                ],
                max_tokens=10,
                temperature=0
            )
            
            return {
                'status': 'healthy',
                'model': self.model,
                'api_accessible': True,
                'response_length': len(response.choices[0].message.content),
                'test_successful': True
            }
            
        except RateLimitError as e:
            logger.warning(f"OpenAI rate limit: {e}")
            return {
                'status': 'degraded',
                'model': self.model,
                'api_accessible': True,
                'error': 'Rate limit exceeded',
                'retry_after': getattr(e, 'retry_after', None)
            }
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                'status': 'unhealthy',
                'model': self.model,
                'api_accessible': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return {
                'status': 'unhealthy',
                'model': self.model,
                'api_accessible': False,
                'error': str(e)
            }
    
    def generate_answer(self, query_request: QueryRequest, 
                       sources: Optional[List[Source]] = None,
                       context: Optional[str] = None) -> QueryResponse:
        """
        Generate answer using GPT-4o-mini with caching.
        
        Args:
            query_request: Query request with parameters
            sources: Retrieved sources for RAG mode
            context: Additional context for the query
            
        Returns:
            Query response with generated answer
            
        Raises:
            GPTServiceError: If answer generation fails
        """
        try:
            # Generate cache key for similar queries
            cache_key = cache_service.generate_key(
                'gpt_answer', 
                query_request.question, 
                query_request.use_rag,
                len(sources) if sources else 0,
                context or '',
                query_request.temperature or 0.7,
                query_request.max_tokens or 1000
            )
            
            # Try to get from cache (only for non-RAG queries to avoid stale data)
            if not query_request.use_rag:
                cached_response = cache_service.get(cache_key)
                if cached_response is not None:
                    logger.debug(f"GPT cache hit for query: {query_request.question[:50]}...")
                    return cached_response
            
            start_time = time.time()
            
            # Create prompt based on mode
            if query_request.use_rag and sources:
                prompt = self._create_rag_prompt(query_request.question, sources, context)
            else:
                prompt = self._create_direct_prompt(query_request.question, context)
            
            # Prepare messages
            messages = [
                {"role": "system", "content": self._get_system_message()},
                {"role": "user", "content": prompt}
            ]
            
            # Generate completion
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=query_request.max_tokens or 1000,
                temperature=query_request.temperature or 0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            # Extract response
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create response
            query_response = QueryResponse(
                question=query_request.question,
                answer=answer,
                sources=sources or [],
                search_type=query_request.search_type,
                total_sources=len(sources) if sources else 0,
                processing_time=processing_time,
                model_used=self.model,
                tokens_used=tokens_used
            )
            
            # Cache non-RAG responses for 1 hour
            if not query_request.use_rag:
                cache_service.set(cache_key, query_response, ttl=3600)
                logger.debug(f"GPT response cached for query: {query_request.question[:50]}...")
            
            logger.info(f"Generated answer: {len(answer)} chars, {tokens_used} tokens, {processing_time:.2f}s")
            return query_response
            
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {e}")
            raise GPTServiceError(f"Rate limit exceeded. Please try again later. {e}")
        except APITimeoutError as e:
            logger.error(f"OpenAI timeout error: {e}")
            raise GPTServiceError(f"Request timed out. Please try again. {e}")
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise GPTServiceError(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            raise GPTServiceError(f"Failed to generate answer: {e}")
    
    def _create_rag_prompt(self, question: str, sources: List[Source], 
                          context: Optional[str] = None) -> str:
        """
        Create prompt for RAG mode with retrieved sources.
        
        Args:
            question: User question
            sources: Retrieved document sources
            context: Additional context
            
        Returns:
            Formatted prompt for RAG mode
        """
        try:
            # Format sources
            sources_text = self._format_sources(sources)
            
            prompt_parts = [
                "You are an expert policy analyst. Answer the following question using the provided policy documents as context.",
                "",
                "QUESTION:",
                question,
                "",
                "CONTEXT FROM POLICY DOCUMENTS:",
                sources_text
            ]
            
            if context:
                prompt_parts.extend([
                    "",
                    "ADDITIONAL CONTEXT:",
                    context
                ])
            
            prompt_parts.extend([
                "",
                "INSTRUCTIONS:",
                "- Answer based primarily on the provided policy documents",
                "- If the answer is not in the documents, clearly state this",
                "- Cite specific documents and sections when possible",
                "- Provide a clear, comprehensive answer",
                "- If multiple documents contain relevant information, synthesize the information",
                "",
                "ANSWER:"
            ])
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Failed to create RAG prompt: {e}")
            raise GPTServiceError(f"Failed to create RAG prompt: {e}")
    
    def _create_direct_prompt(self, question: str, context: Optional[str] = None) -> str:
        """
        Create prompt for direct mode without retrieved sources.
        
        Args:
            question: User question
            context: Additional context
            
        Returns:
            Formatted prompt for direct mode
        """
        try:
            prompt_parts = [
                "You are an expert policy analyst. Answer the following question using your knowledge of policy and governance.",
                "",
                "QUESTION:",
                question
            ]
            
            if context:
                prompt_parts.extend([
                    "",
                    "ADDITIONAL CONTEXT:",
                    context
                ])
            
            prompt_parts.extend([
                "",
                "INSTRUCTIONS:",
                "- Provide a clear, comprehensive answer based on your knowledge",
                "- If you're unsure about specific details, acknowledge this",
                "- Focus on general principles and best practices",
                "- Be helpful and informative",
                "",
                "ANSWER:"
            ])
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Failed to create direct prompt: {e}")
            raise GPTServiceError(f"Failed to create direct prompt: {e}")
    
    def _format_sources(self, sources: List[Source]) -> str:
        """
        Format sources for inclusion in the prompt.
        
        Args:
            sources: List of source objects
            
        Returns:
            Formatted sources text
        """
        try:
            if not sources:
                return "No sources provided."
            
            formatted_sources = []
            for i, source in enumerate(sources, 1):
                source_text = f"[Source {i}] {source.document_name}"
                if source.page_number:
                    source_text += f" (Page {source.page_number})"
                source_text += f"\nRelevance Score: {source.score:.3f}\n"
                source_text += f"Content: {source.content[:500]}..."
                if len(source.content) > 500:
                    source_text += " [truncated]"
                formatted_sources.append(source_text)
            
            return "\n\n".join(formatted_sources)
            
        except Exception as e:
            logger.error(f"Failed to format sources: {e}")
            return "Error formatting sources."
    
    def _get_system_message(self) -> str:
        """
        Get system message for GPT interactions.
        
        Returns:
            System message string
        """
        return """You are PolicyPilot, an expert AI assistant specialized in analyzing policy documents and answering questions about governance, regulations, and policy matters.

Your capabilities include:
- Analyzing policy documents and extracting key information
- Answering questions about governance and regulatory matters
- Providing clear, accurate, and well-structured responses
- Citing sources when available
- Synthesizing information from multiple documents

Guidelines:
- Always be accurate and factual
- Cite specific sources when available
- If you're uncertain about something, acknowledge it
- Provide comprehensive but concise answers
- Use clear, professional language
- Structure your responses logically

You are here to help users understand complex policy matters and navigate regulatory information effectively."""
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the GPT model.
        
        Returns:
            Model information dictionary
        """
        return {
            'model_name': self.model,
            'api_key_configured': bool(self.api_key),
            'client_initialized': self.client is not None,
            'service_type': 'OpenAI GPT'
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the GPT service.
        
        Returns:
            Health check results
        """
        try:
            connection_test = self.check_connection()
            return {
                'status': connection_test['status'],
                'model': self.model,
                'api_accessible': connection_test.get('api_accessible', False),
                'test_successful': connection_test.get('test_successful', False),
                'error': connection_test.get('error')
            }
        except Exception as e:
            logger.error(f"GPT service health check failed: {e}")
            return {
                'status': 'unhealthy',
                'model': self.model,
                'api_accessible': False,
                'error': str(e)
            }
    
    def __del__(self):
        """Cleanup when service is destroyed."""
        try:
            if hasattr(self, 'client') and self.client is not None:
                # OpenAI client doesn't need explicit cleanup
                self.client = None
        except Exception as e:
            logger.warning(f"Error during GPT service cleanup: {e}")
