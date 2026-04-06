"""Extract text from PDFs (one segment per page)."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from policy_pilot.ingestion.preprocess import normalize_text


def load_pdf_pages(path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(path))
    out: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        text = normalize_text(raw)
        if text:
            out.append((i + 1, text))
    return out
