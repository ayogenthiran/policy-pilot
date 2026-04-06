"""
Weaviate: client, collection naming, and chunk schema (application-supplied vectors).
"""

from __future__ import annotations

import re

import weaviate
from weaviate.auth import Auth
from weaviate.classes.config import Configure, DataType, Property

from policy_pilot.config import Settings, get_settings


def library_class_name(slug: str) -> str:
    """Map a slug like policy_documents to a valid Weaviate class name (e.g. Policy_documents)."""
    s = slug.strip()
    s = re.sub(r"[^0-9a-zA-Z_]+", "_", s)
    s = "_".join(p for p in s.split("_") if p)
    if not s:
        return "Document"
    if not s[0].isalpha():
        s = f"C_{s}"
    return s[0].upper() + s[1:]


def _http_endpoint(
    s: Settings,
    *,
    http_host: str | None,
    http_port: int | None,
    http_secure: bool | None,
) -> tuple[str, int, bool]:
    host = http_host if http_host is not None else s.weaviate_http_host
    port = http_port if http_port is not None else s.weaviate_http_port
    secure = http_secure if http_secure is not None else s.weaviate_http_secure
    return host, port, secure


def _grpc_endpoint(
    s: Settings,
    *,
    grpc_host: str | None,
    grpc_port: int | None,
    grpc_secure: bool | None,
) -> tuple[str, int, bool]:
    host = grpc_host if grpc_host is not None else (s.weaviate_grpc_host or s.weaviate_http_host)
    port = grpc_port if grpc_port is not None else s.weaviate_grpc_port
    secure = grpc_secure if grpc_secure is not None else s.weaviate_grpc_secure
    return host, port, secure


def connect_weaviate(
    *,
    http_host: str | None = None,
    http_port: int | None = None,
    http_secure: bool | None = None,
    grpc_host: str | None = None,
    grpc_port: int | None = None,
    grpc_secure: bool | None = None,
) -> weaviate.WeaviateClient:
    """Sync client; explicit args override `Settings` / environment."""
    s = get_settings()
    h_host, h_port, h_secure = _http_endpoint(
        s, http_host=http_host, http_port=http_port, http_secure=http_secure
    )
    g_host, g_port, g_secure = _grpc_endpoint(
        s, grpc_host=grpc_host, grpc_port=grpc_port, grpc_secure=grpc_secure
    )
    key = (s.weaviate_api_key or "").strip()
    auth = Auth.api_key(key) if key else None
    return weaviate.connect_to_custom(
        http_host=h_host,
        http_port=h_port,
        http_secure=h_secure,
        grpc_host=g_host,
        grpc_port=g_port,
        grpc_secure=g_secure,
        auth_credentials=auth,
    )


CHUNK_METADATA_PROPERTIES: list[Property] = [
    Property(name="text", data_type=DataType.TEXT),
    Property(name="source_file", data_type=DataType.TEXT),
    Property(name="file_name", data_type=DataType.TEXT),
    Property(name="page", data_type=DataType.INT),
    Property(name="source", data_type=DataType.TEXT),
]


def delete_collection_if_exists(client: weaviate.WeaviateClient, class_name: str) -> None:
    if client.collections.exists(class_name):
        client.collections.delete(class_name)


def create_chunk_collection(client: weaviate.WeaviateClient, class_name: str) -> None:
    client.collections.create(
        name=class_name,
        vector_config=Configure.Vectors.self_provided(),
        properties=CHUNK_METADATA_PROPERTIES,
    )


def list_collection_names(client: weaviate.WeaviateClient) -> list[str]:
    configs = client.collections.list_all(simple=True)
    return sorted(configs.keys())
