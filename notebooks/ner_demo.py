import json
import os
os.environ["HF_HUB_OFFLINE"] = "0"
import spacy
from gliner import GLiNER
import pandas as pd

# 1. Load the models
print("Loading AI Engines...")
nlp = spacy.load("en_core_web_lg")
# Use the official base model (no login required)
model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")

# 2. The Founder's Exact Paragraph
paragraph = """In fact, the Chinese market has the three most influential names of the retail and tech space – Alibaba, Baidu, and Tencent (collectively touted as BAT), and is betting big in the global AI in retail industry space. The three giants which are claimed to have a cut-throat competition with the U.S. (in terms of resources and capital) are positioning themselves to become the 'future AI' platforms. The trio is also expanding in other Asian countries and investing heavily in the U.S. based AI startups to leverage the power of AI. Backed by such powerful initiatives and presence of these conglomerates, the market in APAC AI is forecast to be the fastest-growing one, with an anticipated CAGR of 45% over 2018-2024."""

# --- EXECUTION ---

# A. spaCy Standard Extraction
print("\n--- spaCy Results (Standard) ---")
doc = nlp(paragraph)
for ent in doc.ents[:10]: # Show first 10
    print(f"{ent.text:25} | {ent.label_}")

# B. GLiNER Custom Extraction (The "Argument" piece)
print("\n--- GLiNER Results (Custom Labels + Confidence) ---")
# We define what we want to find in plain English
labels = ["Company", "Country", "Market Trend", "Percentage"]
entities = model.predict_entities(paragraph, labels)

for e in entities:
    print(f"{e['text']:25} | {e['label']:15} | Score: {round(e['score'], 2)}")

print("\nDemo Complete. Ready for Friday.")
# ---------- Final Structured JSON Logic ----------
result = {
    "chunk_id": "001",
    "source_document": "founder_example_paragraph",
    "chunk_text": doc.text,
    "extraction_status": "supported",
    "spacy_entities": [
        {"text": ent.text, "label": ent.label_}
        for ent in doc.ents
    ],
    "gliner_entities": [
        {
            "text": ent["text"],
            "label": ent["label"],
            "confidence": round(ent["score"], 2),
            "status": (
                "supported" if ent["score"] >= 0.85
                else "review" if ent["score"] >= 0.60
                else "unsupported"
            )
        }
        for ent in entities
    ]
}

print("\n--- Final JSON Output (for backend/Mahlori) ---")
print(json.dumps(result, indent=2))

os.makedirs("examples", exist_ok=True)
with open("examples/sample_output.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print("\nSaved to: examples/sample_output.json")