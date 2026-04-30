"""Shared pipeline: text → spaCy + GLiNER → merged unified entities."""
from __future__ import annotations

import spacy
from gliner import GLiNER

from .merger import merge_entities
from .normalizer import normalize_entity
from .router import route
from .schema import SCHEMA_VERSION

GLINER_LABELS = ["Company", "Country", "Market Trend", "Percentage", "Date", "Amount"]

# Module-level singletons so we don't reload models on every call
_nlp = None
_gliner = None


def _load_models():
    global _nlp, _gliner
    if _nlp is None:
        print("Loading spaCy (en_core_web_lg)...")
        _nlp = spacy.load("en_core_web_lg")
    if _gliner is None:
        print("Loading GLiNER (gliner_medium-v2.1)...")
        _gliner = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")
    return _nlp, _gliner


def _build_entity(text: str, label: str, score: float, start: int, end: int) -> dict:
    score = float(score)
    return {
        "raw": text,
        "normalized": normalize_entity(label, text),
        "label": label,
        "start_char": start,
        "end_char": end,
        "confidence": round(score, 4),
        "status": route(label, score, text).value,
    }


def process_text(
    text: str,
    chunk_id: str = "001",
    source_document: str = "ad_hoc_input",
) -> dict:
    """Run spaCy + GLiNER + dedup; return a v1.2-shaped result dict."""
    nlp, gliner = _load_models()

    doc = nlp(text)
    spacy_entities = [
        _build_entity(ent.text, ent.label_, 1.0, ent.start_char, ent.end_char)
        for ent in doc.ents
    ]

    raw_gliner = gliner.predict_entities(text, GLINER_LABELS)
    gliner_entities = [
        _build_entity(e["text"], e["label"], e["score"], e["start"], e["end"])
        for e in raw_gliner
    ]

    unified = merge_entities(spacy_entities, gliner_entities)

    return {
        "schema_version": SCHEMA_VERSION,
        "chunk_id": chunk_id,
        "source_document": source_document,
        "chunk_text": text,
        "unified_entities": unified,
    }