from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from verification.pipeline import process_text
from verification.schema import SCHEMA_VERSION, Status
from verification.config import PIPELINE_VERSION, MODEL_VERSIONS
from verification.validation import validate_envelope

app = FastAPI(
    title="Olyxee Verification Layer",
    description="NER verification bridge between Mosa (text) and Mahlori (DB). Schema v1.3.",
    version=PIPELINE_VERSION,
)


class VerifyRequest(BaseModel):
    text: str = Field(..., min_length=1)
    chunk_id: str = Field("001")
    source_document: str = Field("inline")


class BatchItem(BaseModel):
    text: str = Field(...)
    chunk_id: str = Field("001")
    source_document: str = Field("inline")


class BatchRequest(BaseModel):
    items: list[BatchItem] = Field(..., min_length=1, max_length=50)


class BatchResultItem(BaseModel):
    chunk_id: str
    status: str
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/")
def root():
    return {
        "service": "Olyxee Verification Layer",
        "schema_version": SCHEMA_VERSION,
        "pipeline_version": PIPELINE_VERSION,
        "endpoints": ["/verify", "/verify/strict", "/verify/batch", "/healthz", "/docs"],
    }


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "schema_version": SCHEMA_VERSION,
        "pipeline_version": PIPELINE_VERSION,
        "model_versions": MODEL_VERSIONS,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/verify")
def verify(req: VerifyRequest):
    try:
        result = process_text(req.text, chunk_id=req.chunk_id, source_document=req.source_document)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")

    errors = validate_envelope(result)
    if errors:
        raise HTTPException(status_code=500, detail={"schema_validation_failed": errors})

    return result


@app.post("/verify/strict")
def verify_strict(req: VerifyRequest):
    try:
        result = process_text(req.text, chunk_id=req.chunk_id, source_document=req.source_document)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")

    errors = validate_envelope(result)
    if errors:
        raise HTTPException(status_code=500, detail={"schema_validation_failed": errors})

    result["unified_entities"] = [
        e for e in result["unified_entities"]
        if e["status"] == Status.SUPPORTED
    ]
    result["audit"]["strict_mode"] = True
    return result


@app.post("/verify/batch")
def verify_batch(req: BatchRequest):
    results: list[BatchResultItem] = []

    for item in req.items:
        if not item.text.strip():
            results.append(BatchResultItem(
                chunk_id=item.chunk_id,
                status="error",
                error="Empty text: nothing to process",
            ))
            continue
        try:
            result = process_text(item.text, chunk_id=item.chunk_id, source_document=item.source_document)
            errors = validate_envelope(result)
            if errors:
                results.append(BatchResultItem(
                    chunk_id=item.chunk_id,
                    status="validation_error",
                    error=f"Schema validation failed: {errors}",
                ))
            else:
                results.append(BatchResultItem(
                    chunk_id=item.chunk_id,
                    status="ok",
                    result=result,
                ))
        except Exception as exc:
            results.append(BatchResultItem(
                chunk_id=item.chunk_id,
                status="error",
                error=str(exc),
            ))

    total = len(results)
    succeeded = sum(1 for r in results if r.status == "ok")

    return {
        "schema_version": SCHEMA_VERSION,
        "summary": {"total": total, "succeeded": succeeded, "failed": total - succeeded},
        "results": [r.model_dump() for r in results],
        "audit": {
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_version": PIPELINE_VERSION,
        },
    }