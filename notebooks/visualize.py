"""Render unified_entities as a color-coded displaCy HTML page."""
import json
import webbrowser
from pathlib import Path

from spacy import displacy

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "examples" / "sample_output.json"
OUTPUT_PATH = ROOT / "examples" / "visualization.html"

STATUS_COLORS = {
    "supported":   "#a8e6a3",  # green  — ready for DB
    "review":      "#ffe082",  # amber  — needs human eyes
    "ambiguous":   "#ffab91",  # orange — engines disagree
    "unsupported": "#cfd8dc",  # gray   — filtered out
}


def main() -> None:
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    text = data["chunk_text"]
    entities = data["unified_entities"]

    # Build displaCy input
    ents, colors = [], {}
    for ent in entities:
        label = f"{ent['label']} • {ent['status']}"
        ents.append({
            "start": ent["start_char"],
            "end": ent["end_char"],
            "label": label,
        })
        colors[label] = STATUS_COLORS.get(ent["status"], "#e0e0e0")

    doc = {"text": text, "ents": ents, "title": None}
    rendered = displacy.render(
        doc, style="ent", manual=True, options={"colors": colors}
    )

    # Stats for the header
    counts = {s: 0 for s in STATUS_COLORS}
    for e in entities:
        counts[e["status"]] = counts.get(e["status"], 0) + 1

    legend = "".join(
        f'<span style="background:{color};padding:4px 12px;border-radius:6px;'
        f'margin-right:12px;font-size:13px;">'
        f'{status} ({counts.get(status,0)})</span>'
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
    print("Opening in browser...")
    webbrowser.open(OUTPUT_PATH.as_uri())


if __name__ == "__main__":
    main()