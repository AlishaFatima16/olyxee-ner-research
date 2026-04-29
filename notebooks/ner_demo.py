import json
import os
import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["HF_HUB_OFFLINE"] = "0"

import spacy
from gliner import GLiNER

from verification.normalizer import normalize_entity
from verification.router import route
from verification.schema import SCHEMA_VERSION


# ---------- Config ----------
GLINER_LABELS = ["Company", "Country", "Market Trend", "Percentage", "Date", "Amount"]
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "examples" / "sample_output.json"

PARAGRAPH = (
    "In fact, the Chinese market has the three most influential names of the retail "
    "and tech space - Alibaba, Baidu, and Tencent (collectively touted as BAT), and "
    "is betting big in the global AI in retail industry space. The three giants which "
    "are claimed to have a cut-throat competition with the U.S. (in terms of resources "
    "and capital) are positioning themselves to become the 'future AI' platforms. The "
    "trio is also expanding in other Asian countries and investing heavily in the U.S. "
    "based AI startups to leverage the power of AI. Backed by such powerful initiatives "
    "and presence of these conglomerates, the market in APAC AI is forecast to be the "
    "fastest-growing one, with an anticipated CAGR of 45% over 2018 - 2024. "
    "To further elaborate on the geographical trends, North America has procured more "
    "than 50% of the global share in 2017 and has been leading the regional landscape "
    "of AI in the retail market. The U.S. has a significant credit in the regional "
    "trends with over 65% of investments (including M&As, private equity, and venture "
    "capital) in artificial intelligence technology. Additionally, the region is a "
    "huge hub for startups in tandem with the presence of tech titans, such as Google, "
    "IBM, and Microsoft."
)


# ---------- Helpers ----------
def build_entity(text: str, label: str, score: float) -> dict:
    score = float(score)
    status = route(label, score, text)
    return {
        "raw": text,
        "normalized": normalize_entity(label, text),
        "label": label,
        "confidence": round(score, 4),
        "status": status.value,
    }


# ---------- Main ----------
def main() -> None:
    print("Loading AI engines...")
    nlp = spacy.load("en_core_web_lg")
    gliner = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")

    # A. spaCy standard extraction (no per-entity scores -> default to 1.0)
    print("\n--- spaCy results (standard) ---")
    doc = nlp(PARAGRAPH)
    spacy_entities = [build_entity(ent.text, ent.label_, 1.0) for ent in doc.ents]
    for ent in spacy_entities[:10]:
        print(f"{ent['raw']:25} | {ent['label']}")

    # B. GLiNER custom extraction (real confidence scores)
    print("\n--- GLiNER results (custom labels + confidence) ---")
    raw_gliner = gliner.predict_entities(PARAGRAPH, GLINER_LABELS)
    gliner_entities = [build_entity(e["text"], e["label"], e["score"]) for e in raw_gliner]
    for ent in gliner_entities:
        print(
            f"{ent['raw']:25} | {ent['label']:15} | "
            f"score={ent['confidence']:.2f} | {ent['status']}"
        )

    # C. Final structured output for the backend (Mahlori)
    result = {
        "schema_version": SCHEMA_VERSION,
        "chunk_id": "001",
        "source_document": "founder_example_paragraph",
        "chunk_text": PARAGRAPH,
        "spacy_entities": spacy_entities,
        "gliner_entities": gliner_entities,
    }

    print("\n--- Final JSON output (for backend/Mahlori) ---")
    print(json.dumps(result, indent=2))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\nSaved to: {OUTPUT_PATH}")
    print("Demo complete.")


if __name__ == "__main__":
    main()