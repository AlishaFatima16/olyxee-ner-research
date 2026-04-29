DEFAULT_THRESHOLDS = {"supported": 0.85, "review": 0.60}

# Stricter for high-stakes labels, looser for fuzzy ones
PER_LABEL_THRESHOLDS = {
    "MONEY":        {"supported": 0.90, "review": 0.70},
    "AMOUNT":       {"supported": 0.90, "review": 0.70},
    "DATE":         {"supported": 0.85, "review": 0.60},
    "PERCENTAGE":   {"supported": 0.80, "review": 0.55},
    "PERCENT":      {"supported": 0.80, "review": 0.55},
    "MARKET TREND": {"supported": 0.75, "review": 0.50},
}

BORDERLINE_BAND = 0.05  # log anything within +/- 5% of a threshold
LOG_PATH = "logs/routing.jsonl"