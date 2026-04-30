DEFAULT_THRESHOLDS = {"supported": 0.85, "review": 0.60}

# Per-label thresholds — surgical, not global. Aligned to Ordo brief.
PER_LABEL_THRESHOLDS = {
    "MONEY":        {"supported": 0.90, "review": 0.70},
    "AMOUNT":       {"supported": 0.90, "review": 0.70},
    "DATE":         {"supported": 0.95, "review": 0.75},  # near-perfect required
    "PERCENTAGE":   {"supported": 0.80, "review": 0.55},
    "PERCENT":      {"supported": 0.80, "review": 0.55},
    "MARKET TREND": {"supported": 0.70, "review": 0.50},  # harder to catch
}

# Labels where normalization is expected; if it returns None we downgrade to 'review'.
NORMALIZABLE_LABELS = {"DATE", "MONEY", "AMOUNT", "PERCENT", "PERCENTAGE"}

BORDERLINE_BAND = 0.05
LOG_PATH = "logs/routing.jsonl"