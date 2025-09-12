"""
Resilience utilities for Policy Pilot RAG backend.
Implements retry logic, circuit breaker pattern, and error handling.
"""

import time
import threading
from typing import Callable, Any, Optional, Dict, List
from enum import Enum
from dataclasses import dataclass
import functools

from src.core.logging import get_logger
from src.utils.exceptions import PolicyPilotException

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryConfig:
    """Retry configuration."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 3
    timeout: float = 30.0


class RetryHandler:
    """Handles retry logic with exponential backoff."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry handler.
        
        Args:
            config: Retry configuration
        """
        self.config = config or RetryConfig()
        self.logger = get_logger(__name__)
    
    def retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                self.logger.debug(f"Retry attempt {attempt + 1}/{self.config.max_attempts} for {func.__name__}")
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                if attempt == self.config.max_attempts - 1:
                    self.logger.error(f"All retry attempts failed for {func.__name__}: {e}")
                    raise e
                
                # Calculate delay
                delay = self._calculate_delay(attempt)
                self.logger.warning(f"Retry attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                
                time.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        if self.config.jitter:
            # Add random jitter to prevent thundering herd
            import random
            jitter = random.uniform(0, delay * 0.1)
            delay += jitter
        
        return delay


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.
        
        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.lock = threading.Lock()
        self.logger = get_logger(__name__)
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise PolicyPilotException("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.logger.info("Circuit breaker reset to CLOSED")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed operation."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.logger.warning("Circuit breaker opened from HALF_OPEN")
            elif self.state == CircuitState.CLOSED and self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        with self.lock:
            return {
                'state': self.state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'last_failure_time': self.last_failure_time
            }


class ResilienceManager:
    """Manages resilience patterns for services."""
    
    def __init__(self):
        """Initialize resilience manager."""
        self.retry_handlers: Dict[str, RetryHandler] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.logger = get_logger(__name__)
    
    def get_retry_handler(self, service_name: str, config: Optional[RetryConfig] = None) -> RetryHandler:
        """
        Get retry handler for service.
        
        Args:
            service_name: Name of the service
            config: Retry configuration
            
        Returns:
            Retry handler for the service
        """
        if service_name not in self.retry_handlers:
            self.retry_handlers[service_name] = RetryHandler(config)
        return self.retry_handlers[service_name]
    
    def get_circuit_breaker(self, service_name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Get circuit breaker for service.
        
        Args:
            service_name: Name of the service
            config: Circuit breaker configuration
            
        Returns:
            Circuit breaker for the service
        """
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(config)
        return self.circuit_breakers[service_name]
    
    def resilient_call(self, service_name: str, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry and circuit breaker.
        
        Args:
            service_name: Name of the service
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        try:
            # Get circuit breaker
            circuit_breaker = self.get_circuit_breaker(service_name)
            
            # Execute through circuit breaker
            return circuit_breaker.call(func, *args, **kwargs)
            
        except Exception as e:
            # If circuit breaker fails, try with retry
            try:
                retry_handler = self.get_retry_handler(service_name)
                return retry_handler.retry(func, *args, **kwargs)
            except Exception as retry_error:
                self.logger.error(f"Resilient call failed for {service_name}: {retry_error}")
                raise retry_error
    
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """
        Get health status for service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service health information
        """
        health = {
            'service_name': service_name,
            'circuit_breaker': None,
            'retry_handler': None
        }
        
        if service_name in self.circuit_breakers:
            health['circuit_breaker'] = self.circuit_breakers[service_name].get_state()
        
        if service_name in self.retry_handlers:
            health['retry_handler'] = {
                'max_attempts': self.retry_handlers[service_name].config.max_attempts,
                'base_delay': self.retry_handlers[service_name].config.base_delay
            }
        
        return health


def retry_on_failure(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator for retry logic.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retry_handler = RetryHandler(RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay
            ))
            return retry_handler.retry(func, *args, **kwargs)
        return wrapper
    return decorator


def circuit_breaker(service_name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0):
    """
    Decorator for circuit breaker pattern.
    
    Args:
        service_name: Name of the service
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time to wait before attempting reset
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            circuit_breaker = CircuitBreaker(CircuitBreakerConfig(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout
            ))
            return circuit_breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Global resilience manager
resilience_manager = ResilienceManager()
