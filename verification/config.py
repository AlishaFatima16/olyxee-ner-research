import os
from pathlib import Path

PIPELINE_VERSION = "1.3.0"

MODEL_VERSIONS = {
    "spacy": "en_core_web_lg-3.7.x",
    "gliner": "urchade/gliner_medium-v2.1",
}

PER_LABEL_THRESHOLDS: dict[str, dict[str, float]] = {
    "DATE":         {"supported": 0.95, "review": 0.75},
    "MONEY":        {"supported": 0.90, "review": 0.70},
    "AMOUNT":       {"supported": 0.90, "review": 0.70},
    "PERCENTAGE":   {"supported": 0.80, "review": 0.55},
    "MARKET TREND": {"supported": 0.70, "review": 0.50},
}

DEFAULT_THRESHOLDS: dict[str, float] = {"supported": 0.85, "review": 0.60}

THRESHOLDS        = PER_LABEL_THRESHOLDS
DEFAULT_THRESHOLD = DEFAULT_THRESHOLDS

BORDERLINE_BAND: float = 0.05

LOG_PATH = Path(os.getenv("ROUTING_LOG_PATH", "logs/routing.jsonl"))