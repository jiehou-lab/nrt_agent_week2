---
name: analyze-tissue
description: Measure how much of a slide is damaged tissue. Use FIRST on any slide, before any classification. Returns numbers and its own confidence. Not for deciding what the damage IS — that is classify-tissue.
---

# Tissue measurement

## Command

    python3 tools/analyze_tissue.py --slide data/<case>.pgm \
        --magnification {10|20|40} \
        --damage-threshold-fraction <0-1> \
        --out results/<case>_analyze.json

`--magnification` is a bare integer: `20`, never `20x`.
`--damage-threshold-fraction` is a fraction: `0.45`, never `45`.

## What comes back

```json
{"n_tiles_tissue": 82, "damage_fraction": 0.451, "hard_edge_rate": 0.11,
 "confidence": 0.55, "low_confidence": true, "usable": true,
 "notes": "elevated edge rate - possible fold or tear"}
```

## How to read it

- `usable: false` — fewer than 40 tissue tiles. **Stop. Do not classify.**
- `low_confidence: true` — the number may be measuring an artifact rather than
  disease. Carry this forward; do not let it disappear.
- `hard_edge_rate` above about 0.08 usually means a fold or tear, not necrosis.

## Privacy

The script opens the image on this machine and prints numbers. The image is
never read into the conversation. Do not open a `.pgm` file yourself.
