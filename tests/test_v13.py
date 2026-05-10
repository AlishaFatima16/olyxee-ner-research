"""
v1.3 test suite
Covers: entity_id, /verify/strict, audit metadata, batch per-item failure isolation
"""
import hashlib
import pytest
from fastapi.testclient import TestClient

from verification.api import app
from verification.merger import merge_entities, _entity_id
from verification.schema import SCHEMA_VERSION, Status
from verification.config import PIPELINE_VERSION, MODEL_VERSIONS
from verification.validation import validate_envelope

client = TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_entity(
    raw="Apple Inc.",
    label="Company",
    start_char=0,
    end_char=10,
    confidence=0.97,
    sources=None,
):
    return {
        "raw": raw,
        "label": label,
        "start_char": start_char,
        "end_char": end_char,
        "confidence": confidence,
        "sources": sources or ["gliner"],
    }


# ── entity_id: format ─────────────────────────────────────────────────────────

def test_entity_id_is_16_chars():
    eid = _entity_id("chunk-001", "Company", 0, 10)
    assert len(eid) == 16


def test_entity_id_is_hex():
    eid = _entity_id("chunk-001", "Company", 0, 10)
    assert all(c in "0123456789abcdef" for c in eid)


# ── entity_id: determinism ────────────────────────────────────────────────────

def test_entity_id_deterministic_same_inputs():
    """Same chunk + label + offsets always produce the same ID."""
    id1 = _entity_id("chunk-001", "Company", 5, 15)
    id2 = _entity_id("chunk-001", "Company", 5, 15)
    assert id1 == id2


def test_entity_id_differs_on_different_offset():
    """Different position → different ID, even for same text and label."""
    id1 = _entity_id("chunk-001", "Company", 0, 10)
    id2 = _entity_id("chunk-001", "Company", 20, 30)
    assert id1 != id2


def test_entity_id_differs_on_different_chunk():
    """Same entity in a different chunk → different ID (important for audit)."""
    id1 = _entity_id("chunk-001", "Company", 0, 10)
    id2 = _entity_id("chunk-002", "Company", 0, 10)
    assert id1 != id2


def test_entity_id_differs_on_different_label():
    """Same offsets but different label → different ID."""
    id1 = _entity_id("chunk-001", "Company", 0, 10)
    id2 = _entity_id("chunk-001", "Country", 0, 10)
    assert id1 != id2


# ── entity_id: uniqueness across merged entities ──────────────────────────────

def test_merged_entity_ids_unique():
    """Two non-overlapping entities in the same merge call get unique IDs."""
    gliner = [
        make_entity("Apple Inc.", "Company", 0, 10, 0.97),
        make_entity("$94.8bn", "Money", 30, 37, 0.93),
    ]
    merged = merge_entities([], gliner, chunk_id="chunk-001")
    ids = [e["entity_id"] for e in merged]
    assert len(ids) == len(set(ids)), "Duplicate entity_ids found"


def test_every_merged_entity_has_entity_id():
    """entity_id is present on every entity output."""
    gliner = [make_entity("Apple", "Company", 0, 5, 0.95)]
    merged = merge_entities([], gliner, chunk_id="chunk-001")
    for entity in merged:
        assert "entity_id" in entity
        assert len(entity["entity_id"]) == 16


# ── Audit metadata ────────────────────────────────────────────────────────────

def test_verify_returns_audit_block():
    resp = client.post("/verify", json={"text": "Apple reported revenue of $2bn in Q3 2025."})
    assert resp.status_code == 200
    body = resp.json()
    assert "audit" in body


def test_audit_has_required_keys():
    resp = client.post("/verify", json={"text": "Revenue grew 12% in January 2025."})
    audit = resp.json()["audit"]
    assert "processed_at" in audit
    assert "pipeline_version" in audit
    assert "model_versions" in audit


def test_audit_pipeline_version_matches_config():
    resp = client.post("/verify", json={"text": "Sales rose 8% to $1.2bn."})
    assert resp.json()["audit"]["pipeline_version"] == PIPELINE_VERSION


def test_audit_model_versions_matches_config():
    resp = client.post("/verify", json={"text": "Maersk cut costs by 15% in 2024."})
    assert resp.json()["audit"]["model_versions"] == MODEL_VERSIONS


def test_audit_processed_at_is_iso8601():
    """processed_at should be a valid ISO 8601 datetime string."""
    from datetime import datetime
    resp = client.post("/verify", json={"text": "Deutsche Bank reported $500m profit."})
    ts = resp.json()["audit"]["processed_at"]
    try:
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        pytest.fail(f"processed_at is not valid ISO 8601: {ts!r}")


# ── /verify/strict ────────────────────────────────────────────────────────────

def test_strict_only_returns_supported():
    resp = client.post("/verify/strict", json={"text": "Apple acquired DeepMind for $1.2bn in Q3 2024."})
    assert resp.status_code == 200
    entities = resp.json()["unified_entities"]
    for e in entities:
        assert e["status"] == Status.supported, (
            f"Non-supported entity found in strict output: {e['raw']} → {e['status']}"
        )


def test_strict_audit_has_strict_mode_flag():
    resp = client.post("/verify/strict", json={"text": "Revenue up 5% to $2bn in December 2024."})
    assert resp.json()["audit"].get("strict_mode") is True


def test_strict_is_subset_of_verify():
    text = "Alibaba revenue grew 8% to $32bn in Q3 2025."
    all_entities = client.post("/verify", json={"text": text}).json()["unified_entities"]
    strict_entities = client.post("/verify/strict", json={"text": text}).json()["unified_entities"]

    all_supported = {e["entity_id"] for e in all_entities if e["status"] == Status.SUPPORTED}
    strict_ids    = {e["entity_id"] for e in strict_entities}

    assert strict_ids == all_supported, (
        "strict endpoint returned entities that are not in the supported set"
    )


def test_strict_returns_empty_list_when_nothing_passes():
    """Text with no high-confidence entities → empty unified_entities, no error."""
    resp = client.post("/verify/strict", json={"text": "Some vague words with no entities."})
    assert resp.status_code == 200
    assert isinstance(resp.json()["unified_entities"], list)


# ── /verify/batch: per-item failure isolation ─────────────────────────────────

def test_batch_isolates_failures():
    """One item with an empty string should fail; others should still succeed."""
    resp = client.post("/verify/batch", json={
        "items": [
            {"text": "Apple revenue grew 8% in Q3 2025.", "chunk_id": "b001"},
            {"text": "", "chunk_id": "b002"},
            {"text": "Maersk cut costs by $500m.", "chunk_id": "b003"},
        ]
    })
    assert resp.status_code == 200
    body = resp.json()
    results = {r["chunk_id"]: r for r in body["results"]}

    assert results["b001"]["status"] == "ok"
    assert results["b003"]["status"] == "ok"
    assert results["b002"]["status"] in ("error", "validation_error")


def test_batch_summary_counts_are_correct():
    resp = client.post("/verify/batch", json={
        "items": [
            {"text": "Revenue grew 12% to $3bn.", "chunk_id": "c001"},
            {"text": "Deutsche Bank profit rose in 2025.", "chunk_id": "c002"},
        ]
    })
    body = resp.json()
    summary = body["summary"]
    assert summary["total"] == 2
    assert summary["succeeded"] + summary["failed"] == summary["total"]


def test_batch_all_items_have_chunk_id():
    resp = client.post("/verify/batch", json={
        "items": [
            {"text": "Apple sales up 8%.", "chunk_id": "d001"},
            {"text": "Revenue $1.2bn in Q4.", "chunk_id": "d002"},
        ]
    })
    for result in resp.json()["results"]:
        assert "chunk_id" in result


def test_batch_respects_50_item_limit():
    """Sending 51 items should return a 422 validation error."""
    items = [{"text": f"Item {i} text with numbers.", "chunk_id": f"item-{i}"} for i in range(51)]
    resp = client.post("/verify/batch", json={"items": items})
    assert resp.status_code == 422


# ── JSON schema validation (validate_envelope) ────────────────────────────────

def test_valid_envelope_passes_validation():
    resp = client.post("/verify", json={"text": "Apple revenue $2bn in Q3 2025."})
    assert resp.status_code == 200
    errors = validate_envelope(resp.json())
    assert errors == [], f"Unexpected validation errors: {errors}"


def test_envelope_missing_audit_fails_validation():
    bad = {
        "schema_version": "1.3",
        "chunk_id": "001",
        "unified_entities": [],
    }
    errors = validate_envelope(bad)
    assert any("audit" in e for e in errors)


def test_envelope_missing_schema_version_fails_validation():
    bad = {
        "chunk_id": "001",
        "unified_entities": [],
        "audit": {
            "processed_at": "2026-05-10T00:00:00+00:00",
            "pipeline_version": "1.3.0",
            "model_versions": {},
        },
    }
    errors = validate_envelope(bad)
    assert any("schema_version" in e for e in errors)


def test_schema_version_is_1_3():
    resp = client.post("/verify", json={"text": "Revenue grew 5% in January 2025."})
    assert resp.json()["schema_version"] == "1.3"