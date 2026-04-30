import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from verification.merger import merge_entities


def _ent(raw, label, start, end, confidence=0.95):
    """Helper to build a pre-merge entity dict."""
    return {
        "raw": raw,
        "normalized": None,
        "label": label,
        "start_char": start,
        "end_char": end,
        "confidence": confidence,
        "status": "supported",
    }


def test_identical_spans_no_conflict():
    """Same span + equivalent labels (ORG <-> Company) -> single entity, no conflict."""
    spacy = [_ent("Apple", "ORG", 0, 5, 1.0)]
    gliner = [_ent("Apple", "Company", 0, 5, 0.97)]

    result = merge_entities(spacy, gliner)

    assert len(result) == 1
    assert result[0]["status"] == "supported"
    assert result[0]["confidence"] == 0.97  # GLiNER score wins
    assert result[0]["sources"] == ["gliner", "spacy"]
    assert "metadata" not in result[0]


def test_longest_span_wins():
    """spaCy 'Apple Inc.' vs GLiNER 'Apple' -> longest span retained."""
    spacy = [_ent("Apple Inc.", "ORG", 0, 10, 1.0)]
    gliner = [_ent("Apple", "Company", 0, 5, 0.96)]

    result = merge_entities(spacy, gliner)

    assert len(result) == 1
    assert result[0]["raw"] == "Apple Inc."
    assert result[0]["start_char"] == 0
    assert result[0]["end_char"] == 10
    assert result[0]["confidence"] == 0.96  # GLiNER score still primary


def test_label_disagreement_marked_ambiguous():
    """Same span, conflicting labels (PERSON vs Company) -> status 'ambiguous'."""
    spacy = [_ent("Tim Cook", "PERSON", 0, 8, 1.0)]
    gliner = [_ent("Tim Cook", "Company", 0, 8, 0.88)]

    result = merge_entities(spacy, gliner)

    assert len(result) == 1
    assert result[0]["status"] == "ambiguous"
    assert "metadata" in result[0]
    assert result[0]["metadata"]["conflicts"] == ["gliner:Company", "spacy:PERSON"]
    # GLiNER's more specific label is preferred
    assert result[0]["label"] == "Company"


def test_overlapping_percent_keeps_approximate():
    """spaCy 'over 65%' (longer) wins; normalization detects 'over' -> approximate=true."""
    spacy = [_ent("over 65%", "PERCENT", 0, 8, 1.0)]
    gliner = [_ent("65%", "Percentage", 5, 8, 0.72)]

    result = merge_entities(spacy, gliner)

    assert len(result) == 1
    assert result[0]["raw"] == "over 65%"
    assert result[0]["normalized"]["value"] == 0.65
    assert result[0]["normalized"]["approximate"] is True


def test_non_overlapping_entities_both_kept():
    """Two distinct spans -> both preserved in unified output."""
    spacy = [_ent("Google", "ORG", 0, 6, 1.0)]
    gliner = [_ent("Microsoft", "Company", 20, 29, 0.95)]

    result = merge_entities(spacy, gliner)

    assert len(result) == 2
    assert {e["raw"] for e in result} == {"Google", "Microsoft"}


def test_empty_entities_returns_empty_list():
    """Paragraph with zero entities should not crash; should return []."""
    assert merge_entities([], []) == []


def test_compound_entity_not_split():
    """
    'New York University' must stay as one entity. Even if spaCy also tags
    'New York' separately as a GPE, the longest span wins and we never emit
    a separate 'New York' entity inside it.
    """
    spacy = [
        {"raw": "New York University", "normalized": None, "label": "ORG",
         "start_char": 0, "end_char": 19, "confidence": 1.0, "status": "supported"},
        {"raw": "New York", "normalized": None, "label": "GPE",
         "start_char": 0, "end_char": 8, "confidence": 1.0, "status": "supported"},
    ]
    gliner = [
        {"raw": "New York University", "normalized": None, "label": "Organization",
         "start_char": 0, "end_char": 19, "confidence": 0.94, "status": "supported"},
    ]

    result = merge_entities(spacy, gliner)

    assert len(result) == 1
    assert result[0]["raw"] == "New York University"
    assert result[0]["start_char"] == 0
    assert result[0]["end_char"] == 19


def test_failed_normalization_downgrades_to_review():
    """
    A DATE entity with high confidence but an unparseable raw string should
    be downgraded from 'supported' to 'review' (Status definition: review
    triggers when normalization fails).
    """
    gliner = [_ent("the third quarter of next yearish", "Date", 0, 33, confidence=0.97)]

    result = merge_entities([], gliner)

    assert len(result) == 1
    assert result[0]["normalized"] is None
    assert result[0]["status"] == "review"