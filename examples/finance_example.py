"""
Finance use case — earnings announcement paragraph.
Run: python examples/finance_example.py
"""
from verification.pipeline import process_text
import json

TEXT = (
    "Apple Inc. reported Q3 2025 revenue of $94.8 billion, up 8% year-over-year, "
    "exceeding analyst estimates of $92.1 billion. Net income rose to $21.4 billion, "
    "with earnings per share of $1.40. The company repurchased $25 billion in shares "
    "during the quarter and raised its dividend by 4% to $0.25 per share. "
    "Management guided Q4 revenue between $88 billion and $92 billion."
)

result = process_text(TEXT, chunk_id="finance-001", source_document="apple_q3_earnings")
print(json.dumps(result, indent=2, default=str))