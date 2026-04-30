from enum import Enum

SCHEMA_VERSION = "1.2"


class Status(str, Enum):
    """
    Lifecycle definitions (Ordo NER contract):

    SUPPORTED   — High confidence, successfully normalized, ready for DB.
    REVIEW      — Confidence in the middle range OR normalization failed
                  (e.g. a weirdly formatted date that we couldn't parse).
    AMBIGUOUS   — High confidence, but spaCy and GLiNER disagree on the label.
    UNSUPPORTED — Low confidence; will be filtered out before DB write.
    """

    SUPPORTED = "supported"
    REVIEW = "review"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"