# Expected results — synthetic histology cases

Run at the recommended demo settings:

```text
magnification = 20
threshold     = 0.45
```

| case | damage_fraction | edge_rate | classification | probability |
|---|---|---|---|---|
| `case_normal_histology` | 0.104 | 0.014 | `normal` | 0.806 |
| `case_mild_injury_histology` | 0.220 | 0.042 | `mild_injury` | 0.700 |
| `case_necrosis_histology` | 0.476 | 0.076 | `necrosis` | 0.943 |
| `case_fold_artifact_histology` | 0.234 | **0.170** | `mild_injury` | 0.700 |

## Reading the fold-artifact case

The fold case returns a perfectly ordinary label — `mild_injury`, with the same
probability the genuine mild-injury case gets. Nothing in the classification
output says anything is wrong.

The only signal is `edge_rate`: **0.170, roughly four times** every other case.
That is the crease in the section, not disease.

This is the case to slow down on:

```text
valid output != equally trustworthy output
```

The classifier was trained on clean slides. It has no artifact class, so it must
return one of the labels it knows. It is not malfunctioning — it is answering the
only question it was built to answer.

## What to notice

- `analyze_tissue.py` reports `edge_rate`. `classify_tissue.py` reports the label.
  They are **two separate commands**, and a person who runs only the second one
  never sees the warning sign.
- Nothing in the package forces the two to be read together. That is a property
  of how the workflow is packaged, not of the science.

*These are synthetic teaching images, not patient data.*
