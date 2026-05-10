import os
from pathlib import Path

PIPELINE_VERSION = "1.3.0"

MODEL_VERSIONS = {
    "spacy": "en_core_web_lg-3.7.x",
    "gliner": "urchade/gliner_medium-v2.1",
}

THRESHOLDS: dict[str, tuple[float, float]] = {
    "DATE":           (0.95, 0.75),
    "MONEY":          (0.90, 0.70),
    "AMOUNT":         (0.90, 0.70),
    "PERCENTAGE":     (0.80, 0.55),
    "MARKET TREND":   (0.70, 0.50),
}

DEFAULT_THRESHOLD: tuple[float, float] = (0.85, 0.60)

BORDERLINE_BAND = 0.05

LOG_PATH = Path(os.getenv("ROUTING_LOG_PATH", "logs/routing.jsonl"))