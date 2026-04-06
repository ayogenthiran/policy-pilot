#!/usr/bin/env python3
"""Ingest a PDF into Weaviate (chunk + OpenAI embeddings). Run from repo root."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from policy_pilot.ingestion import ingest_pdf


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest PDF into Weaviate")
    parser.add_argument("pdf", type=Path, help="Path to PDF file")
    parser.add_argument(
        "--slug",
        type=str,
        default=None,
        help="Collection slug (default: COLLECTION_SLUG from settings / .env)",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop existing collection with this slug before ingesting",
    )
    args = parser.parse_args()
    path = args.pdf
    if not path.is_file():
        print(f"Not a file: {path}", file=sys.stderr)
        return 1
    try:
        n = ingest_pdf(path, collection_slug=args.slug, recreate_collection=args.recreate)
        print(f"Ingested {n} chunks from {path.name}")
        return 0
    except Exception as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
