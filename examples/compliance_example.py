"""
Compliance use case — regulatory disclosure paragraph.
Run: python examples/compliance_example.py
"""
from verification.pipeline import process_text
import json

TEXT = (
    "Under the EU AI Act (effective August 2024), all high-risk AI systems deployed "
    "in the European Union must be registered in the EU database by March 2026. "
    "Non-compliance carries fines of up to €30 million or 6% of global annual turnover, "
    "whichever is higher. Deutsche Bank AG confirmed it completed its internal compliance "
    "audit on 15 January 2025, covering 142 AI systems across 38 jurisdictions."
)

result = process_text(TEXT, chunk_id="compliance-001", source_document="eu_ai_act_disclosure")
print(json.dumps(result, indent=2, default=str))