"""Environment-backed settings (`.env` optional)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""

    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    rag_top_k: int = 5
    # Hybrid: BM25 + HNSW vector. 1.0 = pure vector, 0.0 = pure keyword.
    rag_hybrid_alpha: float = Field(default=0.75, ge=0.0, le=1.0)
    # Comma-separated Weaviate property names for the BM25 leg (e.g. text,file_name).
    rag_hybrid_bm25_properties: str = "text"

    weaviate_http_host: str = "localhost"
    weaviate_http_port: int = 8080
    weaviate_http_secure: bool = False
    # Empty means same host as HTTP (typical for docker-compose / local).
    weaviate_grpc_host: str = ""
    weaviate_grpc_port: int = 50051
    weaviate_grpc_secure: bool = False
    weaviate_api_key: str | None = None

    # Default knowledge base: mapped to Weaviate class via library_class_name (see vectordb).
    collection_slug: str = "policy_documents"

    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 64


@lru_cache
def get_settings() -> Settings:
    return Settings()
