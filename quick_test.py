from gliner import GLiNER

# This uses a tiny model (only ~200MB) just to test logic
model = GLiNER.from_pretrained("numind/EntitySieve_gliner_tiny")

text = "Alibaba's revenue grew by 45% between 2018 and 2024."
labels = ["company", "percentage", "date"]

entities = model.predict_entities(text, labels)

for entity in entities:
    print(f"Entity: {entity['text']} | Label: {entity['label']} | Confidence: {entity['score']:.2f}")