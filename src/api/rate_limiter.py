"""
Rate limiting middleware for Policy Pilot RAG backend.
Implements token bucket algorithm for API rate limiting.
"""

import time
import threading
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
import hashlib

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from src.core.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(self, requests_per_minute: int = 60, burst_size: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst requests allowed
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.tokens_per_second = requests_per_minute / 60.0
        self.buckets: Dict[str, Dict[str, float]] = {}
        self.lock = threading.Lock()
        
        logger.info(f"RateLimiter initialized: {requests_per_minute} req/min, burst={burst_size}")
    
    def is_allowed(self, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed for client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            with self.lock:
                current_time = time.time()
                
                # Get or create bucket for client
                if client_id not in self.buckets:
                    self.buckets[client_id] = {
                        'tokens': self.burst_size,
                        'last_refill': current_time
                    }
                
                bucket = self.buckets[client_id]
                
                # Refill tokens based on time passed
                time_passed = current_time - bucket['last_refill']
                tokens_to_add = time_passed * self.tokens_per_second
                bucket['tokens'] = min(self.burst_size, bucket['tokens'] + tokens_to_add)
                bucket['last_refill'] = current_time
                
                # Check if request is allowed
                if bucket['tokens'] >= 1:
                    bucket['tokens'] -= 1
                    return True, {
                        'allowed': True,
                        'remaining_tokens': int(bucket['tokens']),
                        'reset_time': current_time + (1 / self.tokens_per_second)
                    }
                else:
                    return False, {
                        'allowed': False,
                        'remaining_tokens': 0,
                        'reset_time': current_time + (1 / self.tokens_per_second),
                        'retry_after': 1 / self.tokens_per_second
                    }
                
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Allow request if rate limiter fails
            return True, {'allowed': True, 'error': str(e)}
    
    def get_client_id(self, request: Request) -> str:
        """
        Get client identifier from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client identifier
        """
        try:
            # Try to get client IP
            client_ip = request.client.host if request.client else "unknown"
            
            # Try to get user agent
            user_agent = request.headers.get("user-agent", "unknown")
            
            # Create unique client ID
            client_data = f"{client_ip}:{user_agent}"
            client_id = hashlib.md5(client_data.encode()).hexdigest()
            
            return client_id
            
        except Exception as e:
            logger.error(f"Failed to get client ID: {e}")
            return "unknown"
    
    def cleanup_old_buckets(self, max_age: int = 3600) -> int:
        """
        Clean up old client buckets.
        
        Args:
            max_age: Maximum age in seconds
            
        Returns:
            Number of buckets removed
        """
        try:
            with self.lock:
                current_time = time.time()
                old_buckets = []
                
                for client_id, bucket in self.buckets.items():
                    if current_time - bucket['last_refill'] > max_age:
                        old_buckets.append(client_id)
                
                for client_id in old_buckets:
                    del self.buckets[client_id]
                
                if old_buckets:
                    logger.info(f"Cleaned up {len(old_buckets)} old rate limit buckets")
                
                return len(old_buckets)
                
        except Exception as e:
            logger.error(f"Failed to cleanup old buckets: {e}")
            return 0


class AdvancedRateLimiter:
    """Advanced rate limiter with different limits for different endpoints."""
    
    def __init__(self):
        """Initialize advanced rate limiter."""
        self.limiters: Dict[str, RateLimiter] = {}
        self.endpoint_limits = {
            'upload': {'requests_per_minute': 10, 'burst_size': 3},
            'query': {'requests_per_minute': 30, 'burst_size': 10},
            'search': {'requests_per_minute': 60, 'burst_size': 15},
            'health': {'requests_per_minute': 120, 'burst_size': 30},
            'default': {'requests_per_minute': 60, 'burst_size': 10}
        }
        
        logger.info("AdvancedRateLimiter initialized")
    
    def get_limiter(self, endpoint: str) -> RateLimiter:
        """
        Get rate limiter for endpoint.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Rate limiter for the endpoint
        """
        try:
            # Determine endpoint type
            endpoint_type = self._get_endpoint_type(endpoint)
            
            if endpoint_type not in self.limiters:
                limits = self.endpoint_limits.get(endpoint_type, self.endpoint_limits['default'])
                self.limiters[endpoint_type] = RateLimiter(
                    requests_per_minute=limits['requests_per_minute'],
                    burst_size=limits['burst_size']
                )
            
            return self.limiters[endpoint_type]
            
        except Exception as e:
            logger.error(f"Failed to get limiter for endpoint {endpoint}: {e}")
            return self.limiters.get('default', RateLimiter())
    
    def _get_endpoint_type(self, endpoint: str) -> str:
        """
        Get endpoint type from path.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Endpoint type
        """
        try:
            if '/upload' in endpoint:
                return 'upload'
            elif '/query' in endpoint:
                return 'query'
            elif '/search' in endpoint:
                return 'search'
            elif '/health' in endpoint:
                return 'health'
            else:
                return 'default'
                
        except Exception:
            return 'default'
    
    def is_allowed(self, request: Request) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            endpoint = request.url.path
            limiter = self.get_limiter(endpoint)
            client_id = limiter.get_client_id(request)
            
            return limiter.is_allowed(client_id)
            
        except Exception as e:
            logger.error(f"Rate limiting check failed: {e}")
            return True, {'allowed': True, 'error': str(e)}


# Global rate limiter instances
rate_limiter = RateLimiter()
advanced_rate_limiter = AdvancedRateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI.
    
    Args:
        request: FastAPI request
        call_next: Next middleware in chain
        
    Returns:
        Response or rate limit error
    """
    try:
        # Check rate limit
        is_allowed, rate_info = advanced_rate_limiter.is_allowed(request)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": rate_info.get('retry_after', 60),
                    "rate_limit_info": rate_info
                },
                headers={
                    "Retry-After": str(int(rate_info.get('retry_after', 60))),
                    "X-RateLimit-Limit": str(advanced_rate_limiter.endpoint_limits.get('default', {}).get('requests_per_minute', 60)),
                    "X-RateLimit-Remaining": str(rate_info.get('remaining_tokens', 0)),
                    "X-RateLimit-Reset": str(int(rate_info.get('reset_time', time.time() + 60)))
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(advanced_rate_limiter.endpoint_limits.get('default', {}).get('requests_per_minute', 60))
        response.headers["X-RateLimit-Remaining"] = str(rate_info.get('remaining_tokens', 0))
        response.headers["X-RateLimit-Reset"] = str(int(rate_info.get('reset_time', time.time() + 60)))
        
        return response
        
    except Exception as e:
        logger.error(f"Rate limiting middleware error: {e}")
        # Allow request if middleware fails
        return await call_next(request)
