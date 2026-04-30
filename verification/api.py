"""FastAPI server exposing the Verification Layer over HTTP."""
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .pipeline import _load_models, process_text
from .schema import SCHEMA_VERSION


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load models on startup so the first /verify call isn't slow.
    print("Pre-loading NER models...")
    _load_models()
    print("Models ready. Verification Layer is up.")
    yield


app = FastAPI(
    title="Olyxee Verification Layer",
    description=(
        "NER verification bridge between Mosa (unstructured text) and "
        "Mahlori (structured backend). Hybrid spaCy + GLiNER pipeline "
        "with coordinate-based deduplication and per-entity confidence routing."
    ),
    version=SCHEMA_VERSION,
    lifespan=lifespan,
)


class VerifyRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Paragraph to verify.")
    chunk_id: str = Field("001", description="Chunk identifier.")
    source_document: str = Field("api_input", description="Source document name.")


class BatchVerifyRequest(BaseModel):
    chunks: List[VerifyRequest] = Field(..., min_length=1, max_length=50)


@app.get("/", tags=["meta"])
def root():
    """Service overview."""
    return {
        "service": "Olyxee Verification Layer",
        "schema_version": SCHEMA_VERSION,
        "endpoints": {
            "POST /verify": "Run NER + dedup on a single text chunk",
            "POST /verify/batch": "Run NER + dedup on up to 50 chunks at once",
            "GET /healthz": "Liveness probe",
            "GET /docs": "Interactive API docs (Swagger UI)",
        },
    }


@app.get("/healthz", tags=["meta"])
def healthz():
    """Liveness probe for orchestration / Mahlori health checks."""
    return {"status": "ok", "schema_version": SCHEMA_VERSION}


@app.post("/verify", tags=["verification"])
def verify(req: VerifyRequest):
    """Process a single text chunk and return the unified entities envelope."""
    try:
        return process_text(
            req.text,
            chunk_id=req.chunk_id,
            source_document=req.source_document,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Verification failed: {exc}")


@app.post("/verify/batch", tags=["verification"])
def verify_batch(req: BatchVerifyRequest):
    """Process multiple chunks in one call (max 50)."""
    results = []
    for chunk in req.chunks:
        try:
            results.append(process_text(
                chunk.text,
                chunk_id=chunk.chunk_id,
                source_document=chunk.source_document,
            ))
        except Exception as exc:
            results.append({
                "chunk_id": chunk.chunk_id,
                "error": str(exc),
                "schema_version": SCHEMA_VERSION,
            })
    return {"schema_version": SCHEMA_VERSION, "results": results}