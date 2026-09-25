# tissue_analyzer

Quantification of tissue damage on whole-slide histology images, with
classification into normal / mild injury / necrosis.

Hou Lab, Michigan State University

## Installation

```bash
git clone <repo>
cd tissue_analyzer
pip install -r requirements.txt
```

## Usage

Parameters can come from the command line, from a config file, or both.
Command line wins, then the config file, then the built-in defaults.

```bash
# uses config/analysis.yaml for everything but the slide
python scripts/analyze_tissue.py --slide data/case_003.pgm

# everything explicit
python scripts/analyze_tissue.py \
    --slide data/case_003.pgm \
    --magnification 20 \
    --threshold 0.45 \
    --out results/case_003.json

# a different config for a different scanner
python scripts/analyze_tissue.py --slide s1.pgm --config config/aperio.yaml
```

| flag | meaning | default |
|---|---|---|
| `--slide` | path to the slide (required) | — |
| `--magnification` | 10, 20 or 40 | config, else 20 |
| `--threshold` | grey **fraction** below which a tile is damaged | config, else 0.45 |
| `--min-tiles` | warn below this many tissue tiles | config, else 40 |
| `--config` | parameter file | `config/analysis.yaml` |
| `--out` | write here; `.json` writes JSON, otherwise text | — |
| `--quiet` | suppress the printed summary | off |

`--threshold` is a **fraction between 0 and 1**, not a percentage.

Classify a slide:

```bash
python scripts/classify_tissue.py --slide data/case_003.pgm
```

Batch over everything in `data/`:

```bash
bash scripts/run_batch.sh
```

## Configuration

`config/analysis.yaml` holds the defaults:

| key | meaning | default |
|---|---|---|
| `magnification` | tile size; 10, 20 or 40 | 20 |
| `damage_threshold` | grey fraction below which a tile counts as damaged | 0.45 |
| `min_tiles` | below this the estimate is unstable | 40 |
| `edge_spread_cutoff` | tile grey range suggesting a fold | 140 |

## Model

`models/tissue_rf_v2.json` — random forest, 1,200 training slides,
0.91 balanced accuracy on held-out clean slides.

**Important:** the training set excluded slides with folds, tears and pen marks,
so the model has no artifact class. On an artifact-containing slide it will
return one of its three labels anyway, usually with high probability. Always
check the edge rate reported by `analyze_tissue.py` before trusting a label.
See `models/model_card.md`.

## Output

`analyze_tissue.py` prints a summary and writes `results/<slide>_analysis.txt`.

`classify_tissue.py` prints the label and the model's probability.

## Layout

```
tissue_analyzer/
├── README.md
├── requirements.txt
├── config/analysis.yaml
├── models/           tissue_rf_v2.json, model_card.md
├── data/             example slides
├── scripts/          analyze_tissue.py, classify_tissue.py, run_batch.sh
└── results/          outputs land here
```

## Citation

Hou Lab (2026). tissue_analyzer: tile-based damage quantification for
whole-slide histology. Internal tool.
