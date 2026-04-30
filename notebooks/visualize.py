"""
Render unified_entities as a color-coded displaCy HTML page.

Usage:
  python notebooks/visualize.py                       # use existing sample_output.json
  python notebooks/visualize.py --text "Apple bought OpenAI for $5bn in 2024."
  python notebooks/visualize.py --file path/to/input.txt
"""
from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from spacy import displacy

DEFAULT_INPUT = ROOT / "examples" / "sample_output.json"
OUTPUT_PATH = ROOT / "examples" / "visualization.html"

STATUS_COLORS = {
    "supported":   "#a8e6a3",
    "review":      "#ffe082",
    "ambiguous":   "#ffab91",
    "unsupported": "#cfd8dc",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize Olyxee Verification Layer output.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text", help="Run pipeline on a paragraph passed inline.")
    group.add_argument("--file", help="Run pipeline on the contents of a .txt file.")
    parser.add_argument(
        "--no-open", action="store_true", help="Skip opening the browser."
    )
    return parser.parse_args()


def _load_data(args: argparse.Namespace) -> dict:
    if args.text:
        from verification.pipeline import process_text
        return process_text(args.text, source_document="cli_text_input")

    if args.file:
        path = Path(args.file)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        from verification.pipeline import process_text
        return process_text(path.read_text(encoding="utf-8"), source_document=path.name)

    if not DEFAULT_INPUT.exists():
        raise FileNotFoundError(
            f"No --text/--file given and {DEFAULT_INPUT} doesn't exist. "
            "Run `python notebooks/ner_demo.py` first, or pass --text."
        )
    return json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))


def main() -> None:
    args = _parse_args()
    data = _load_data(args)

    text = data["chunk_text"]
    entities = data["unified_entities"]

    ents, colors = [], {}
    for ent in entities:
        label = f"{ent['label']} • {ent['status']}"
        ents.append({
            "start": ent["start_char"],
            "end": ent["end_char"],
            "label": label,
        })
        colors[label] = STATUS_COLORS.get(ent["status"], "#e0e0e0")

    rendered = displacy.render(
        {"text": text, "ents": ents, "title": None},
        style="ent",
        manual=True,
        options={"colors": colors},
    )

    counts = {s: 0 for s in STATUS_COLORS}
    for e in entities:
        counts[e["status"]] = counts.get(e["status"], 0) + 1

    legend = "".join(
        f'<span style="background:{color};padding:4px 12px;border-radius:6px;'
        f'margin-right:12px;font-size:13px;">{status} ({counts.get(status,0)})</span>'
        for status, color in STATUS_COLORS.items()
    )

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Olyxee Verification Layer — Visualization</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      max-width: 1000px; margin: 40px auto; padding: 0 24px; color: #1a1a1a;
    }}
    h1 {{ color: #1a237e; margin-bottom: 4px; }}
    .meta {{ color: #555; margin-bottom: 24px; font-size: 14px; }}
    .legend {{
      background: #fafafa; padding: 16px 20px; border-radius: 8px;
      margin: 20px 0 32px; border: 1px solid #eee;
    }}
    .legend h3 {{ margin: 0 0 12px; font-size: 15px; color: #444; }}
    .definitions {{ margin-top: 24px; font-size: 13px; color: #666; }}
    .definitions p {{ margin: 4px 0; }}
  </style>
</head>
<body>
  <h1>Olyxee Verification Layer</h1>
  <div class="meta">
    Source: <strong>{data['source_document']}</strong> &nbsp;·&nbsp;
    Schema: <strong>v{data['schema_version']}</strong> &nbsp;·&nbsp;
    Entities: <strong>{len(entities)}</strong>
  </div>

  <div class="legend">
    <h3>Status</h3>
    {legend}
    <div class="definitions">
      <p><strong>supported</strong> — high confidence, normalized, ready for DB</p>
      <p><strong>review</strong> — mid confidence or normalization failed</p>
      <p><strong>ambiguous</strong> — spaCy and GLiNER disagree on the label</p>
      <p><strong>unsupported</strong> — below threshold, will be filtered</p>
    </div>
  </div>

  {rendered}
</body>
</html>
"""

    OUTPUT_PATH.write_text(full_html, encoding="utf-8")
    print(f"Saved visualization to: {OUTPUT_PATH}")
    if not args.no_open:
        print("Opening in browser...")
        webbrowser.open(OUTPUT_PATH.as_uri())


if __name__ == "__main__":
    main()