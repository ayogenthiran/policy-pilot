"""
Configuration settings for Policy Pilot RAG backend.
Uses pydantic_settings for environment variable management.
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key for GPT models")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    
    # OpenSearch Configuration
    opensearch_url: str = Field(default="http://localhost:9200", description="OpenSearch server URL")
    opensearch_index: str = Field(default="policy_documents", description="OpenSearch index name")
    
    # Document Processing Settings
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Maximum file size in bytes (10MB)")
    chunk_size: int = Field(default=1000, description="Text chunk size for processing")
    chunk_overlap: int = Field(default=200, description="Overlap between text chunks")
    
    # API Settings
    cors_origins: List[str] = Field(default=["http://localhost:3000"], description="Allowed CORS origins")
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    
    # Embedding Model
    embedding_model: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
        description="Sentence transformer model for embeddings"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/policy_pilot.log", description="Log file path")
    
    # File Upload Settings
    upload_dir: str = Field(default="uploads", description="Directory for uploaded files")
    data_dir: str = Field(default="data", description="Directory for processed data")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
