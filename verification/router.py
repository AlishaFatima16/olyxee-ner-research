import json
import os
from datetime import datetime, timezone

from .config import (
    BORDERLINE_BAND,
    DEFAULT_THRESHOLDS,
    LOG_PATH,
    PER_LABEL_THRESHOLDS,
)
from .schema import Status


def _thresholds_for(label: str) -> dict:
    return PER_LABEL_THRESHOLDS.get(label.upper(), DEFAULT_THRESHOLDS)


def _log_borderline(label: str, raw: str, score: float, threshold: float, kind: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "label": label,
        "raw": raw,
        "confidence": score,
        "threshold": threshold,
        "kind": kind,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def route(label: str, score: float, raw: str) -> Status:
    """Per-label confidence routing with borderline logging."""
    th = _thresholds_for(label)

    if score >= th["supported"]:
        status = Status.SUPPORTED
    elif score >= th["review"]:
        status = Status.REVIEW
    else:
        status = Status.UNSUPPORTED

    for name, value in th.items():
        if abs(score - value) <= BORDERLINE_BAND:
            _log_borderline(label, raw, score, value, kind=f"near_{name}")
            break

    return status