#!/usr/bin/env python3
"""Weaviate utilities: readiness, list/create/delete chunk collections."""

from __future__ import annotations

import argparse
import sys

from policy_pilot.vectordb import (
    connect_weaviate,
    create_chunk_collection,
    delete_collection_if_exists,
    library_class_name,
    list_collection_names,
)


def cmd_ready() -> int:
    client = connect_weaviate()
    try:
        client.collections.list_all(simple=True)
        print("Weaviate is reachable")
        return 0
    except Exception as exc:
        print(f"Weaviate check failed: {exc}")
        return 1
    finally:
        client.close()


def cmd_list() -> int:
    client = connect_weaviate()
    try:
        for name in list_collection_names(client):
            print(name)
        return 0
    finally:
        client.close()


def cmd_create(slug: str) -> int:
    class_name = library_class_name(slug)
    client = connect_weaviate()
    try:
        if client.collections.exists(class_name):
            print(f"Collection already exists: {class_name}")
            return 0
        create_chunk_collection(client, class_name)
        print(f"Created collection: {class_name} (slug={slug!r})")
        return 0
    finally:
        client.close()


def cmd_delete(slug: str) -> int:
    class_name = library_class_name(slug)
    client = connect_weaviate()
    try:
        delete_collection_if_exists(client, class_name)
        print(f"Removed if it existed: {class_name}")
        return 0
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Weaviate VectorDB utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ready", help="Verify Weaviate is reachable")
    sub.add_parser("list", help="List collection names")

    p_create = sub.add_parser("create", help="Create chunk collection from slug")
    p_create.add_argument("slug", help="e.g. policy_documents → Weaviate class name")

    p_delete = sub.add_parser("delete", help="Delete collection by slug")
    p_delete.add_argument("slug")

    args = parser.parse_args()
    if args.cmd == "ready":
        return cmd_ready()
    if args.cmd == "list":
        return cmd_list()
    if args.cmd == "create":
        return cmd_create(args.slug)
    if args.cmd == "delete":
        return cmd_delete(args.slug)
    return 2


if __name__ == "__main__":
    sys.exit(main())
