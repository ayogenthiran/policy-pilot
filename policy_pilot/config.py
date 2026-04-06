"""Environment-backed settings (`.env` optional)."""

from __future__ import annotations

from functools import lru_cache

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

    weaviate_http_host: str = "localhost"
    weaviate_http_port: int = 8080
    weaviate_http_secure: bool = False
    # Empty means same host as HTTP (typical for docker-compose / local).
    weaviate_grpc_host: str = ""
    weaviate_grpc_port: int = 50051
    weaviate_grpc_secure: bool = False
    weaviate_api_key: str | None = None

    collection_slug: str = "policy_documents"

    chunk_size: int = 1200
    chunk_overlap: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()
