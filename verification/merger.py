from typing import List

from .config import NORMALIZABLE_LABELS
from .normalizer import normalize_entity
from .router import route
from .schema import Status

LABEL_EQUIVALENCE = {
    "ORG": "Company",
    "Company": "Company",
    "GPE": "Country",
    "LOC": "Country",
    "Country": "Country",
    "PERSON": "Person",
    "Person": "Person",
    "DATE": "Date",
    "Date": "Date",
    "PERCENT": "Percentage",
    "PERCENTAGE": "Percentage",
    "Percentage": "Percentage",
    "MONEY": "Money",
    "AMOUNT": "Money",
    "Amount": "Money",
    "NORP": "Group",
    "CARDINAL": "Number",
    "Market Trend": "Market Trend",
}


def _canonical_label(label: str) -> str:
    return LABEL_EQUIVALENCE.get(label, label)


def _group_overlapping(entities: List[dict]) -> List[List[dict]]:
    sorted_ents = sorted(entities, key=lambda e: (e["start_char"], -e["end_char"]))
    groups, current, current_end = [], [], -1
    for ent in sorted_ents:
        if ent["start_char"] < current_end:
            current.append(ent)
            current_end = max(current_end, ent["end_char"])
        else:
            if current:
                groups.append(current)
            current = [ent]
            current_end = ent["end_char"]
    if current:
        groups.append(current)
    return groups


def _pick_canonical_span(group: List[dict]) -> dict:
    """Longest span wins. Ties broken by GLiNER preference."""
    return max(
        group,
        key=lambda e: (e["end_char"] - e["start_char"], e["source"] == "gliner"),
    )


def _pick_label(group: List[dict], canonical: dict) -> str:
    """
    On label disagreement, prefer GLiNER's label — it's the more specific
    custom-trained label (Company > ORG, Country > GPE, etc.).
    """
    gliner_in_group = [e for e in group if e["source"] == "gliner"]
    if gliner_in_group:
        return max(gliner_in_group, key=lambda e: e["confidence"])["label"]
    return canonical["label"]


def _best_score(group: List[dict]) -> float:
    gliner_scores = [e["confidence"] for e in group if e["source"] == "gliner"]
    if gliner_scores:
        return max(gliner_scores)
    return max(e["confidence"] for e in group)


def merge_entities(spacy_list: List[dict], gliner_list: List[dict]) -> List[dict]:
    """Combine spaCy + GLiNER entities into a single deduplicated, unified list."""
    tagged = (
        [{**e, "source": "spacy"} for e in spacy_list]
        + [{**e, "source": "gliner"} for e in gliner_list]
    )
    if not tagged:
        return []

    unified = []
    for group in _group_overlapping(tagged):
        canonical = _pick_canonical_span(group)
        score = _best_score(group)
        chosen_label = _pick_label(group, canonical)

        canonical_labels = {_canonical_label(e["label"]) for e in group}
        is_ambiguous = len(canonical_labels) > 1

        # Re-normalize on the canonical (longest) raw text so approximate
        # markers ("over", "more than") are captured even if GLiNER missed them.
        normalized = normalize_entity(chosen_label, canonical["raw"])

        # Status decision (in priority order)
        if is_ambiguous:
            status = Status.AMBIGUOUS.value
        else:
            status = route(chosen_label, score, canonical["raw"]).value
            # Downgrade to 'review' if normalization was expected but failed
            if (
                status == Status.SUPPORTED.value
                and chosen_label.upper() in NORMALIZABLE_LABELS
                and normalized is None
            ):
                status = Status.REVIEW.value

        entity = {
            "raw": canonical["raw"],
            "normalized": normalized,
            "label": chosen_label,
            "start_char": canonical["start_char"],
            "end_char": canonical["end_char"],
            "confidence": round(float(score), 4),
            "status": status,
            "sources": sorted({e["source"] for e in group}),
        }

        if is_ambiguous:
            entity["metadata"] = {
                "conflicts": sorted({f"{e['source']}:{e['label']}" for e in group})
            }

        unified.append(entity)

    return unified