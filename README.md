# Olyxee NER Research & Verification

A Proof of Concept (POC) for the Alisha Layer, focusing on extracting structured entities from unstructured RAG chunks and applying confidence-based verification.

## 🛠 Tech Stack
- **spaCy (Large):** High-speed baseline extraction.
- **GLiNER:** Zero-shot NER for custom compliance fields.
- **Python 3.12+**

## 📊 Logic: Confidence Routing
- **> 0.85:** Auto-Verified (Direct to Backend)
- **0.60 - 0.85:** LLM Fallback (Secondary Check)
- **< 0.60:** Human Review Required

## 🚀 Usage
1. Activate environment: `.\venv\Scripts\activate`
2. Run baseline: `python ner_demo.py`