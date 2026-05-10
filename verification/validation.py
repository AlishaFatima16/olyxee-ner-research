"""JSON schema definition for unified_entities output validation."""

ENTITY_SCHEMA = {
    "type": "object",
    "required": ["entity_id", "raw", "label", "start_char", "end_char", "confidence", "status", "sources"],
    "properties": {
        "entity_id":   {"type": "string", "minLength": 16, "maxLength": 16},
        "raw":         {"type": "string", "minLength": 1},
        "normalized":  {},
        "label":       {"type": "string", "minLength": 1},
        "start_char":  {"type": "integer", "minimum": 0},
        "end_char":    {"type": "integer", "minimum": 1},
        "confidence":  {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "status":      {"type": "string", "enum": ["supported", "review", "ambiguous", "unsupported"]},
        "sources":     {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "metadata":    {"type": "object"},
    },
    "additionalProperties": False,
}

ENVELOPE_SCHEMA = {
    "type": "object",
    "required": ["schema_version", "chunk_id", "unified_entities", "audit"],
    "properties": {
        "schema_version":   {"type": "string"},
        "chunk_id":         {"type": "string"},
        "source_document":  {"type": "string"},
        "chunk_text":       {"type": "string"},
        "unified_entities": {"type": "array", "items": ENTITY_SCHEMA},
        "audit": {
            "type": "object",
            "required": ["processed_at", "pipeline_version", "model_versions"],
            "properties": {
                "processed_at":    {"type": "string"},
                "pipeline_version":{"type": "string"},
                "model_versions":  {"type": "object"},
            },
        },
    },
}


def validate_envelope(envelope: dict) -> list[str]:
    """
    Returns a list of validation errors.
    Empty list means valid.
    Uses jsonschema if installed, falls back to manual checks.
    """
    try:
        import jsonschema
        errors = list(jsonschema.Draft7Validator(ENVELOPE_SCHEMA).iter_errors(envelope))
        return [e.message for e in errors]
    except ImportError:
        errors = []
        for field in ENVELOPE_SCHEMA["required"]:
            if field not in envelope:
                errors.append(f"Missing required field: {field}")
        for entity in envelope.get("unified_entities", []):
            for field in ENTITY_SCHEMA["required"]:
                if field not in entity:
                    errors.append(f"Entity missing required field: {field} in entity {entity.get('raw', '?')}")
        return errors