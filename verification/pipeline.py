from __future__ import annotations
from datetime import datetime, timezone
import spacy
from gliner import GLiNER
from verification.schema import SCHEMA_VERSION
from verification.config import PIPELINE_VERSION, MODEL_VERSIONS
from verification.merger import merge_entities

_nlp = None
_gliner = None

GLINER_LABELS = [
    "Company", "Person", "Country", "City", "Date",
    "Money", "Percentage", "Market Trend", "Product",
]


def _load_models():
    global _nlp, _gliner
    if _nlp is None:
        _nlp = spacy.load("en_core_web_lg")
    if _gliner is None:
        _gliner = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")


def _spacy_entities(text: str) -> list[dict]:
    doc = _nlp(text)
    return [
        {
            "raw": ent.text,
            "label": ent.label_,
            "start_char": ent.start_char,
            "end_char": ent.end_char,
            "confidence": 0.80,
            "sources": ["spacy"],
        }
        for ent in doc.ents
    ]


def _gliner_entities(text: str) -> list[dict]:
    results = _gliner.predict_entities(text, GLINER_LABELS)
    return [
        {
            "raw": r["text"],
            "label": r["label"],
            "start_char": r["start"],
            "end_char": r["end"],
            "confidence": round(r["score"], 4),
            "sources": ["gliner"],
        }
        for r in results
    ]


def process_text(
    text: str,
    chunk_id: str = "001",
    source_document: str = "inline",
) -> dict:
    _load_models()

    spacy_ents = _spacy_entities(text)
    gliner_ents = _gliner_entities(text)
    unified = merge_entities(spacy_ents, gliner_ents, chunk_id=chunk_id)

    return {
        "schema_version": SCHEMA_VERSION,
        "chunk_id": chunk_id,
        "source_document": source_document,
        "chunk_text": text,
        "unified_entities": unified,
        "audit": {
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_version": PIPELINE_VERSION,
            "model_versions": MODEL_VERSIONS,
        },
    }