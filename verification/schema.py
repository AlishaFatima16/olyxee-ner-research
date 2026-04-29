from enum import Enum

SCHEMA_VERSION = "1.1"


class Status(str, Enum):
    SUPPORTED = "supported"      # high confidence, model is sure
    REVIEW = "review"            # medium confidence, human glance needed
    AMBIGUOUS = "ambiguous"      # multiple valid interpretations (e.g. "May" = month or person)
    UNSUPPORTED = "unsupported"  # low confidence, do not act on
    CONFLICT = "conflict"        # spaCy and GLiNER disagree on label