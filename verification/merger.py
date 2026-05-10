from __future__ import annotations
import hashlib
from typing import Any
from verification.schema import Status
from verification.router import route_entity
from verification.normalizer import normalize


def _entity_id(chunk_id: str, label: str, start_char: int, end_char: int) -> str:
    """Deterministic 16-char hex ID — same entity in same text always gets same ID."""
    key = f"{chunk_id}:{label}:{start_char}:{end_char}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _overlap(a: dict, b: dict) -> bool:
    return a["start_char"] < b["end_char"] and b["start_char"] < a["end_char"]


def _span_len(e: dict) -> int:
    return e["end_char"] - e["start_char"]


def _canonicalize_label(label: str) -> str:
    mapping = {
        "ORG": "Company", "GPE": "Country", "LOC": "Location",
        "PERSON": "Person", "MONEY": "Money", "DATE": "Date",
        "PERCENT": "Percentage",
    }
    return mapping.get(label.upper(), label)


def merge_entities(
    spacy_entities: list[dict],
    gliner_entities: list[dict],
    chunk_id: str = "unknown",
) -> list[dict]:
    all_entities = list(spacy_entities) + list(gliner_entities)
    if not all_entities:
        return []

    all_entities.sort(key=lambda e: e["start_char"])

    groups: list[list[dict]] = []
    for entity in all_entities:
        placed = False
        for group in groups:
            if any(_overlap(entity, member) for member in group):
                group.append(entity)
                placed = True
                break
        if not placed:
            groups.append([entity])

    merged: list[dict] = []
    for group in groups:
        canonical = max(group, key=_span_len)

        gliner_members = [e for e in group if "gliner" in e.get("sources", [])]
        if gliner_members:
            primary = max(gliner_members, key=_span_len)
            confidence = primary["confidence"]
        else:
            confidence = canonical.get("confidence", 0.0)

        sources = sorted({s for e in group for s in e.get("sources", [])})

        all_labels = {_canonicalize_label(e["label"]) for e in group}
        canonical_label = _canonicalize_label(canonical["label"])

        conflicts = None
        if len(all_labels) > 1:
            conflicts = sorted({
                f"{s}:{e['label']}"
                for e in group
                for s in e.get("sources", [])
            })

        raw = canonical["raw"]
        normalized = normalize(raw, canonical_label)

        status = route_entity(
            label=canonical_label,
            confidence=confidence,
            normalized=normalized,
            raw=raw,
            conflicts=conflicts,
        )

        entity_out: dict[str, Any] = {
            "entity_id": _entity_id(chunk_id, canonical_label, canonical["start_char"], canonical["end_char"]),
            "raw": raw,
            "normalized": normalized,
            "label": canonical_label,
            "start_char": canonical["start_char"],
            "end_char": canonical["end_char"],
            "confidence": round(confidence, 4),
            "status": status,
            "sources": sources,
        }

        if conflicts:
            entity_out["metadata"] = {"conflicts": conflicts}

        merged.append(entity_out)

    merged.sort(key=lambda e: e["start_char"])
    return merged