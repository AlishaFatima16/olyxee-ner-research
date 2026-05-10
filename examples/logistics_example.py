"""
Logistics use case — supply chain disruption report.
Run: python examples/logistics_example.py
"""
from verification.pipeline import process_text
import json

TEXT = (
    "Maersk reported a 12% increase in shipping costs from Shanghai to Rotterdam "
    "following Red Sea disruptions in early 2025. Transit times extended by approximately "
    "14 days, adding an estimated $1,800 per container in fuel surcharges. "
    "DHL Express rerouted 34% of its Asia-Europe cargo through the Cape of Good Hope, "
    "increasing CO2 emissions by roughly 22% per shipment. "
    "Freight rates on the Asia-Europe corridor peaked at $5,200 per TEU in February 2025."
)

result = process_text(TEXT, chunk_id="logistics-001", source_document="supply_chain_q1_2025")
print(json.dumps(result, indent=2, default=str))