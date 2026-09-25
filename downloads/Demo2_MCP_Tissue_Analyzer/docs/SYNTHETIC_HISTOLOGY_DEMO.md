# Synthetic histology-like image set for the Tissue Analyzer demos

These are **synthetic teaching images**, not patient data and not a medically validated dataset.

The grayscale `.pgm` files are designed to work with the existing `tile_stats()` implementation and the existing `tissue_rf_v2.json` decision boundaries. Color PNG files in `previews/` are derived from the same synthetic morphology and are provided only for visually nicer lecture/demo display.

## Recommended demo settings

```text
magnification = 20
threshold / damage_threshold_fraction = 0.45
```

## Expected results with the existing model

| Image | Damage fraction | Edge rate | Expected class | Model probability |
|---|---:|---:|---|---:|
| `case_normal_histology.pgm` | 0.104 | 0.014 | `normal` | 0.806 |
| `case_mild_injury_histology.pgm` | 0.220 | 0.042 | `mild_injury` | 0.700 |
| `case_necrosis_histology.pgm` | 0.476 | 0.076 | `necrosis` | 0.943 |
| `case_fold_artifact_histology.pgm` | 0.234 | 0.170 | `mild_injury` | 0.700 |

The fold-artifact case is intentionally included to demonstrate an elevated edge-rate / lower-confidence warning in the MCP analysis.

## Important limitation

The current "model" is intentionally simple. It classifies from `damage_fraction` using fixed boundaries:

```text
normal       < 0.15
mild_injury  < 0.35
necrosis     >= 0.35
```

This is appropriate for an agent/MCP classroom demonstration, but it is **not a real pathology model** and should not be represented as clinically meaningful.
