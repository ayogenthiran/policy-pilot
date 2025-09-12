"""
Production configuration for Policy Pilot RAG backend.
Environment-specific settings and optimizations for production deployment.
"""

import os
from typing import List, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings


class ProductionSettings(BaseSettings):
    """Production-specific settings."""
    
    # Environment
    environment: str = Field(default="production", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    workers: int = Field(default=4, description="Number of worker processes")
    
    # Security
    cors_origins: List[str] = Field(
        default=["https://policypilot.ai", "https://www.policypilot.ai"],
        description="Allowed CORS origins for production"
    )
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration")
    
    # Database
    opensearch_url: str = Field(default="https://opensearch:9200", description="OpenSearch URL")
    opensearch_username: str = Field(default="admin", description="OpenSearch username")
    opensearch_password: str = Field(..., description="OpenSearch password")
    opensearch_index: str = Field(default="policy_documents_prod", description="OpenSearch index")
    
    # OpenAI
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model")
    openai_timeout: int = Field(default=60, description="OpenAI request timeout")
    openai_max_retries: int = Field(default=3, description="OpenAI max retries")
    
    # File Upload
    max_file_size: int = Field(default=50 * 1024 * 1024, description="Max file size (50MB)")
    upload_dir: str = Field(default="/app/uploads", description="Upload directory")
    data_dir: str = Field(default="/app/data", description="Data directory")
    
    # Caching
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    cache_max_size: int = Field(default=10000, description="Max cache entries")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, description="Rate limit per minute")
    rate_limit_burst_size: int = Field(default=10, description="Rate limit burst size")
    
    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_file: str = Field(default="/app/logs/policy_pilot.log", description="Log file path")
    log_format: str = Field(default="json", description="Log format (json/text)")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    
    # Performance
    embedding_batch_size: int = Field(default=64, description="Embedding batch size")
    max_concurrent_requests: int = Field(default=100, description="Max concurrent requests")
    request_timeout: int = Field(default=300, description="Request timeout in seconds")
    
    # Circuit Breaker
    circuit_breaker_failure_threshold: int = Field(default=5, description="Circuit breaker failure threshold")
    circuit_breaker_recovery_timeout: int = Field(default=60, description="Circuit breaker recovery timeout")
    
    # Health Checks
    health_check_interval: int = Field(default=30, description="Health check interval")
    health_check_timeout: int = Field(default=10, description="Health check timeout")
    
    class Config:
        env_file = ".env.production"
        env_file_encoding = "utf-8"
        case_sensitive = False


class DevelopmentSettings(BaseSettings):
    """Development-specific settings."""
    
    # Environment
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=True, description="Debug mode")
    
    # API Configuration
    api_host: str = Field(default="127.0.0.1", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    workers: int = Field(default=1, description="Number of worker processes")
    
    # Security
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins for development"
    )
    secret_key: str = Field(default="dev-secret-key", description="Secret key for JWT tokens")
    access_token_expire_minutes: int = Field(default=60, description="Access token expiration")
    
    # Database
    opensearch_url: str = Field(default="http://localhost:9200", description="OpenSearch URL")
    opensearch_username: str = Field(default="", description="OpenSearch username")
    opensearch_password: str = Field(default="", description="OpenSearch password")
    opensearch_index: str = Field(default="policy_documents_dev", description="OpenSearch index")
    
    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model")
    openai_timeout: int = Field(default=30, description="OpenAI request timeout")
    openai_max_retries: int = Field(default=2, description="OpenAI max retries")
    
    # File Upload
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Max file size (10MB)")
    upload_dir: str = Field(default="uploads", description="Upload directory")
    data_dir: str = Field(default="data", description="Data directory")
    
    # Caching
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    cache_max_size: int = Field(default=1000, description="Max cache entries")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=120, description="Rate limit per minute")
    rate_limit_burst_size: int = Field(default=20, description="Rate limit burst size")
    
    # Logging
    log_level: str = Field(default="DEBUG", description="Log level")
    log_file: str = Field(default="logs/policy_pilot.log", description="Log file path")
    log_format: str = Field(default="text", description="Log format (json/text)")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    
    # Performance
    embedding_batch_size: int = Field(default=16, description="Embedding batch size")
    max_concurrent_requests: int = Field(default=50, description="Max concurrent requests")
    request_timeout: int = Field(default=120, description="Request timeout in seconds")
    
    # Circuit Breaker
    circuit_breaker_failure_threshold: int = Field(default=3, description="Circuit breaker failure threshold")
    circuit_breaker_recovery_timeout: int = Field(default=30, description="Circuit breaker recovery timeout")
    
    # Health Checks
    health_check_interval: int = Field(default=10, description="Health check interval")
    health_check_timeout: int = Field(default=5, description="Health check timeout")
    
    class Config:
        env_file = ".env.development"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> BaseSettings:
    """
    Get settings based on environment.
    
    Returns:
        Settings instance for current environment
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()
