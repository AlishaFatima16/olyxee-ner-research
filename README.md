# Olyxee Verification Layer

> NER verification bridge between **Mosa** (unstructured text) and **Mahlori** (structured backend).
> Hybrid spaCy + GLiNER pipeline with coordinate-based deduplication, per-entity confidence routing, and typed normalization.

**Schema version:** `1.2`
**Status:** Production-ready core module for the Ordo NER pipeline.

---

## What this layer does

```
┌──────────┐      ┌──────────────────────┐      ┌──────────┐
│  Mosa    │ ───► │  Verification Layer  │ ───► │ Mahlori  │
│  (text)  │      │  (this repo)         │      │  (DB)    │
└──────────┘      └──────────────────────┘      └──────────┘
```

It takes a raw paragraph and returns a single, deduplicated list of entities where every entry has:

- **Character offsets** (`start_char`, `end_char`) — ready for displaCy / UI rendering
- **A typed `normalized` object** — not a raw string (e.g. dates → `{iso, precision}`, money → `{currency, amount}`)
- **A `status`** decided by per-entity-type confidence thresholds
- **`sources`** showing which engine(s) found it (spaCy, GLiNER, or both)
- **`metadata.conflicts`** when the engines disagreed on the label

---

## Status lifecycle

| Status        | Meaning                                                                 |
|---------------|-------------------------------------------------------------------------|
| `supported`   | High confidence, successfully normalized, ready for the database        |
| `review`      | Mid confidence OR normalization failed (e.g. unparseable date)          |
| `ambiguous`   | High confidence, but spaCy and GLiNER disagree on the label             |
| `unsupported` | Below threshold; will be filtered out before DB write                   |

---

## Per-entity confidence thresholds

Defined in `verification/config.py`. No more global `0.85` — each label gets a surgical threshold:

| Label          | `supported` ≥ | `review` ≥ |
|----------------|---------------|------------|
| DATE           | 0.95          | 0.75       |
| MONEY / AMOUNT | 0.90          | 0.70       |
| PERCENTAGE     | 0.80          | 0.55       |
| MARKET TREND   | 0.70          | 0.50       |
| (default)      | 0.85          | 0.60       |

Borderline calls (within ±0.05 of any threshold) are auto-logged to `logs/routing.jsonl` for future tuning.

---

## Output schema (v1.2)

```json
{
  "schema_version": "1.2",
  "chunk_id": "001",
  "source_document": "founder_example_paragraph",
  "chunk_text": "...",
  "unified_entities": [
    {
      "raw": "over 65%",
      "normalized": { "type": "percentage", "value": 0.65, "approximate": true },
      "label": "Percentage",
      "start_char": 971,
      "end_char": 979,
      "confidence": 0.72,
      "status": "review",
      "sources": ["gliner", "spacy"]
    },
    {
      "raw": "Alibaba",
      "normalized": null,
      "label": "Company",
      "start_char": 96,
      "end_char": 103,
      "confidence": 0.97,
      "status": "ambiguous",
      "sources": ["gliner", "spacy"],
      "metadata": { "conflicts": ["gliner:Company", "spacy:GPE"] }
    }
  ]
}
```

---

## Project structure

```
olyxee-ner-research/
├── verification/              # Core package
│   ├── __init__.py
│   ├── schema.py              # SCHEMA_VERSION, Status enum, definitions
│   ├── config.py              # Per-entity thresholds, borderline band, log path
│   ├── normalizer.py          # Date / Money / Percentage typed normalization
│   ├── router.py              # Confidence -> status routing + borderline logging
│   ├── merger.py              # Coordinate-based dedup + conflict detection
│   ├── pipeline.py            # End-to-end: text -> unified entities
│   └── api.py                 # FastAPI server (POST /verify, /verify/batch)
├── notebooks/
│   ├── ner_demo.py            # CLI demo on the founder example paragraph
│   └── visualize.py           # Color-coded HTML visualizer
├── tests/                     # 35 test cases
│   ├── test_dates.py
│   ├── test_money.py
│   ├── test_percent.py
│   └── test_merger.py
├── examples/
│   ├── sample_output.json     # Latest demo output
│   └── visualization.html     # Latest rendered visualization
├── logs/
│   └── routing.jsonl          # Borderline confidence calls (auto-generated)
├── requirements.txt
└── README.md
```

---

## Setup (Windows / PowerShell)

```powershell
git clone https://github.com/AlishaFatima16/olyxee-ner-research.git
cd olyxee-ner-research

python -m venv venv
.\venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

First-time GLiNER model download (~500 MB) happens automatically on first run.

---

## Usage

### 1. Run the demo on the founder example paragraph

```powershell
python notebooks/ner_demo.py
```

Outputs the unified entity list to the terminal and saves `examples/sample_output.json`.

### 2. Visualize the output (color-coded HTML)

```powershell
# From the existing sample_output.json
python notebooks/visualize.py

# From an inline paragraph
python notebooks/visualize.py --text "Apple acquired DeepMind for $1.2bn in Q3 2024, growing AI revenue by over 45%."

# From a text file
python notebooks/visualize.py --file path/to/input.txt
```

Saves and auto-opens `examples/visualization.html`. Entities are color-coded:

- Green = `supported`
- Amber = `review`
- Orange = `ambiguous`
- Gray = `unsupported`

### 3. Run the REST API

```powershell
uvicorn verification.api:app --reload --port 8000
```

Then open:

- **http://localhost:8000/docs** — interactive Swagger UI
- **http://localhost:8000/healthz** — liveness probe
- **http://localhost:8000/** — service overview

#### API endpoints

| Method | Path             | Purpose                                               |
|--------|------------------|-------------------------------------------------------|
| GET    | `/`              | Service overview                                      |
| GET    | `/healthz`       | Liveness probe (returns `{status, schema_version}`)   |
| POST   | `/verify`        | Process one chunk -> unified entities envelope        |
| POST   | `/verify/batch`  | Process up to 50 chunks in one call                   |
| GET    | `/docs`          | Swagger UI (auto-generated from the OpenAPI spec)     |

#### Example call (PowerShell)

```powershell
Invoke-RestMethod -Uri http://localhost:8000/verify `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"text": "Apple acquired DeepMind for $1.2bn in Q3 2024."}' `
  | ConvertTo-Json -Depth 10
```

#### Example call (curl)

```bash
curl -X POST http://localhost:8000/verify \
  -H "Content-Type: application/json" \
  -d '{"text": "Apple acquired DeepMind for $1.2bn in Q3 2024."}'
```

### 4. Run the test suite

```powershell
pytest tests/ -v
```

35 tests covering dates, money, percentages, overlap behavior, compound entities (`New York University` doesn't get split), empty input, and failed-normalization downgrades.

---

## How dedup works (the merge logic)

When spaCy and GLiNER both find entities in the same paragraph:

1. **Group overlapping spans** by character offset
2. **Pick the longest span** as canonical (so `Apple Inc.` beats `Apple`)
3. **Use GLiNER's confidence** as the primary score (it has real probabilities, spaCy doesn't)
4. **Prefer GLiNER's label** as the more specific custom-trained label (`Company` over `ORG`, `Country` over `GPE`)
5. **Detect label disagreement** — if labels don't canonicalize to the same thing, status becomes `ambiguous` and `metadata.conflicts` lists both
6. **Re-run normalization** on the canonical (longest) raw text — so approximate markers like `over` or `more than` are captured even if GLiNER missed them

---

## Tech stack

- **Python 3.11**
- **spaCy** + `en_core_web_lg` — standard NER for broad coverage
- **GLiNER** + `urchade/gliner_medium-v2.1` — custom-label NER with real confidence scores
- **dateparser** — flexible date string parsing
- **pytest** — defensive test suite (35 cases)
- **FastAPI** + **uvicorn** — REST API with auto-generated OpenAPI docs

---

## Versions shipped

| Version | Highlights                                                                            |
|---------|---------------------------------------------------------------------------------------|
| v1.0    | Normalizer, confidence routing, structured JSON output                                |
| v1.1    | Typed normalization, schema versioning, per-label thresholds, borderline logging      |
| v1.2    | Coordinate-based dedup, char offsets, ambiguous status, displaCy visualizer, REST API |

---

## Author

**Alisha Fatima** — Verification Layer for the Ordo NER pipeline at Olyxee.
