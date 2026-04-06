"""FastAPI app: health and RAG query (Streamlit or other clients can call this)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from policy_pilot import __version__
from policy_pilot.rag.service import query_rag

app = FastAPI(title="Policy Pilot RAG", version=__version__)


class QueryBody(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    collection_slug: str | None = None
    top_k: int | None = Field(None, ge=1, le=50)


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def post_query(body: QueryBody) -> QueryResponse:
    try:
        out = query_rag(
            body.question,
            collection_slug=body.collection_slug,
            top_k=body.top_k,
        )
        return QueryResponse(answer=out["answer"], sources=out["sources"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
