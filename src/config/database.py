"""
Database configuration for Policy Pilot RAG backend.
Handles OpenSearch connection management and configuration with connection pooling.
"""

import time
import threading
from typing import Dict, Any, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import OpenSearchException, ConnectionError, NotFoundError
from urllib3.util.retry import Retry
from urllib3.poolmanager import PoolManager

from src.config.settings import settings
from src.core.logging import get_logger
from src.utils.exceptions import OpenSearchError, ConfigurationError

logger = get_logger(__name__)


class OpenSearchConnection:
    """Singleton class for managing OpenSearch connections with connection pooling."""
    
    _instance: Optional['OpenSearchConnection'] = None
    _client: Optional[OpenSearch] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'OpenSearchConnection':
        """Ensure singleton pattern with thread safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the OpenSearch connection with pooling."""
        if not hasattr(self, '_initialized'):
            with self._lock:
                if not hasattr(self, '_initialized'):
                    self._initialized = True
                    self.opensearch_url = settings.opensearch_url
                    self.index_name = settings.opensearch_index
                    self._connection_config = self._get_connection_config()
                    self._last_health_check = 0
                    self._health_check_interval = 30  # Check every 30 seconds
                    logger.info(f"OpenSearchConnection initialized with pooling: {self.opensearch_url}")
    
    def _get_connection_config(self) -> Dict[str, Any]:
        """
        Get OpenSearch connection configuration with advanced pooling.
        
        Returns:
            Dictionary with connection configuration
        """
        try:
            # Parse URL to extract host and port
            url_parts = self.opensearch_url.replace('http://', '').replace('https://', '')
            if ':' in url_parts:
                host, port = url_parts.split(':', 1)
                port = int(port)
            else:
                host = url_parts
                port = 9200
            
            # Determine if using HTTPS
            use_ssl = self.opensearch_url.startswith('https://')
            
            # Configure retry strategy
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
                backoff_factor=1,
                raise_on_status=False
            )
            
            # Configure connection pooling
            pool_manager = PoolManager(
                num_pools=10,
                maxsize=20,
                block=False,
                retries=retry_strategy,
                timeout=30
            )
            
            config = {
                'hosts': [{'host': host, 'port': port}],
                'use_ssl': use_ssl,
                'verify_certs': use_ssl,
                'ssl_assert_hostname': False,
                'ssl_show_warn': False,
                'timeout': 30,
                'max_retries': 3,
                'retry_on_timeout': True,
                'http_compress': True,
                'http_auth': None,
                'connection_class': RequestsHttpConnection,
                'pool_maxsize': 20,
                'pool_block': False,
                'maxsize': 20,
                'headers': {
                    'User-Agent': 'PolicyPilot-RAG/1.0',
                    'Connection': 'keep-alive'
                },
                'http_auth': None,
                'connection_pool_class': None,  # Use default
                'pool_manager': pool_manager
            }
            
            # Add authentication if configured
            if hasattr(settings, 'opensearch_username') and hasattr(settings, 'opensearch_password'):
                config['http_auth'] = (settings.opensearch_username, settings.opensearch_password)
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to create connection config: {e}")
            raise ConfigurationError(f"Failed to create OpenSearch connection configuration: {e}")
    
    def get_client(self) -> OpenSearch:
        """
        Get OpenSearch client instance with connection pooling and health checks.
        
        Returns:
            OpenSearch client instance
            
        Raises:
            OpenSearchError: If client creation fails
        """
        try:
            with self._lock:
                if self._client is None:
                    logger.info("Creating new OpenSearch client with connection pooling")
                    self._client = OpenSearch(**self._connection_config)
                    
                    # Test connection
                    self._test_connection()
                
                # Periodic health check
                current_time = time.time()
                if current_time - self._last_health_check > self._health_check_interval:
                    self._test_connection()
                    self._last_health_check = current_time
                
                return self._client
            
        except Exception as e:
            logger.error(f"Failed to create OpenSearch client: {e}")
            raise OpenSearchError(f"Failed to create OpenSearch client: {e}")
    
    def _test_connection(self) -> None:
        """
        Test the OpenSearch connection.
        
        Raises:
            OpenSearchError: If connection test fails
        """
        try:
            if self._client is None:
                return
            
            # Simple ping test
            self._client.ping()
            logger.debug("OpenSearch connection test successful")
            
        except Exception as e:
            logger.error(f"OpenSearch connection test failed: {e}")
            # Reset client to force reconnection
            self._client = None
            raise OpenSearchError(f"OpenSearch connection test failed: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on OpenSearch connection.
        
        Returns:
            Health check results
            
        Raises:
            OpenSearchError: If health check fails
        """
        try:
            if self._client is None:
                self._client = OpenSearch(**self._connection_config)
            
            # Get cluster health
            health_info = self._client.cluster.health()
            
            # Get cluster info
            cluster_info = self._client.info()
            
            # Check if index exists
            index_exists = self._client.indices.exists(index=self.index_name)
            
            health_status = {
                'status': 'healthy' if health_info['status'] in ['green', 'yellow'] else 'unhealthy',
                'cluster_status': health_info['status'],
                'cluster_name': cluster_info['cluster_name'],
                'opensearch_version': cluster_info['version']['number'],
                'index_exists': index_exists,
                'connection_url': self.opensearch_url,
                'index_name': self.index_name
            }
            
            logger.info(f"OpenSearch health check: {health_status['status']}")
            return health_status
            
        except ConnectionError as e:
            logger.error(f"OpenSearch connection error: {e}")
            return {
                'status': 'unhealthy',
                'error': 'Connection failed',
                'connection_url': self.opensearch_url,
                'details': str(e)
            }
        except OpenSearchException as e:
            logger.error(f"OpenSearch error: {e}")
            return {
                'status': 'unhealthy',
                'error': 'OpenSearch error',
                'connection_url': self.opensearch_url,
                'details': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error during health check: {e}")
            return {
                'status': 'unhealthy',
                'error': 'Unexpected error',
                'connection_url': self.opensearch_url,
                'details': str(e)
            }
    
    def close_connection(self) -> None:
        """Close the OpenSearch connection."""
        try:
            if self._client is not None:
                # OpenSearch client doesn't have explicit close method
                # but we can clear the reference
                self._client = None
                logger.info("OpenSearch connection closed")
        except Exception as e:
            logger.warning(f"Error closing OpenSearch connection: {e}")
    
    def reset_connection(self) -> None:
        """Reset the connection (close and clear client)."""
        try:
            self.close_connection()
            self._client = None
            logger.info("OpenSearch connection reset")
        except Exception as e:
            logger.warning(f"Error resetting OpenSearch connection: {e}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information.
        
        Returns:
            Dictionary with connection information
        """
        return {
            'opensearch_url': self.opensearch_url,
            'index_name': self.index_name,
            'client_initialized': self._client is not None,
            'connection_config': {
                'hosts': self._connection_config['hosts'],
                'use_ssl': self._connection_config['use_ssl'],
                'timeout': self._connection_config['timeout']
            }
        }
    
    def __del__(self):
        """Cleanup when connection is destroyed."""
        try:
            self.close_connection()
        except Exception as e:
            logger.warning(f"Error during OpenSearch connection cleanup: {e}")


# Global connection instance
opensearch_connection = OpenSearchConnection()
