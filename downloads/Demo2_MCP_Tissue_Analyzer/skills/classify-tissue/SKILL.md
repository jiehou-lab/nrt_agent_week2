---
name: classify-tissue
description: Label a measured slide as normal, mild_injury or necrosis using tissue_rf_v2. Use AFTER analyze-tissue, and only when that reported usable. It cannot detect artifacts and answers confidently even when the input is unusable.
---

# Tissue classifier (tissue_rf_v2)

## Command

    python3 tools/classify_tissue.py \
        --features results/<case>_analyze.json \
        --out results/<case>_classify.json

It takes the **measurement**, not the slide. That is deliberate: it means the
measurement's warning cannot be lost on the way in.

## What comes back

```json
{"label": "necrosis", "probability": 0.935,
 "classes_the_model_knows": ["normal", "mild_injury", "necrosis"],
 "model_card": "clean slides only; folds, tears and pen marks excluded",
 "upstream_low_confidence": true,
 "upstream_notes": "elevated edge rate - possible fold or tear"}
```

## Read the model card before you trust the number

Trained on clean slides only. Folds, tears and pen marks were excluded, so
**there is no artifact class it could return**. Shown an artifact it still picks
one of three labels, with a high probability.

`probability: 0.935` means "of my three classes, this fits best" — **not** "I am
93.5% likely to be right".

## Rules

- `upstream_low_confidence: true` → do not report the label as a finding. Report
  it as "the classifier said X, but the measurement was flagged unreliable".
- Never round a probability into words like "almost certainly".
