# Two packages, one analysis

`tissue_analyzer/` and `tissue_analyzer_mcp/` do **exactly the same science**.
Same slides, same model file, same tile arithmetic. Run both on `case_003` and
you get the same 45.1% damage, the same 82 tiles, the same necrosis at 0.935.

The difference is entirely in the packaging — and the point of showing them side
by side is that the second one is not more sophisticated, it is just **legible to
something that cannot ask you questions**.

---

## What each folder looks like

```
tissue_analyzer/                        tissue_analyzer_mcp/
├── README.md         ← read once       ├── README.md
├── requirements.txt                    ├── MIGRATION.md   ← what changed
├── config/                             ├── server.py      ← NEW: announces the tools
│   └── analysis.yaml ← hidden params   ├── .mcp.json      ← NEW: how to attach it
├── models/                             ├── models/        ← IDENTICAL
│   ├── tissue_rf_v2.json               │   ├── tissue_rf_v2.json
│   └── model_card.md                   │   └── model_card.md
├── data/             ← IDENTICAL       ├── data/          ← IDENTICAL
├── scripts/                            ├── tools/         ← same maths, JSON out
│   ├── analyze_tissue.py               │   ├── analyze_tissue.py
│   ├── classify_tissue.py              │   ├── classify_tissue.py
│   ├── common.py                       │   └── common.py  ← byte-identical
│   └── run_batch.sh                    ├── skills/        ← NEW: a card per tool
└── results/                            ├── agents/        ← NEW: the stopping rules
                                        ├── commands/      ← NEW: /analyze-slide
                                        └── results/
```

Three folders are identical. One is rewritten. Three are new.

---

## The same run, both ways

### tissue_analyzer

```bash
$ python scripts/analyze_tissue.py --slide data/case_003.pgm --magnification 20

====================================================
  Tissue Damage Analysis
  Slide: case_003.pgm
====================================================
  Magnification:             20x
  Tissue tiles analysed:     82
  Damaged tiles:             37
  Damage fraction:           45.1%
  Hard edge rate:            11.0%
====================================================
  Note: elevated edge rate - check slide for folds

$ python scripts/classify_tissue.py --slide data/case_003.pgm

  Slide:          case_003.pgm
  Damage:         45.1%
  Classification: NECROSIS (93.5% confidence)
  Model:          tissue_rf_v2
```

**Look at what just happened.** The first command warned about a fold. The second
command never saw that warning — it re-reads the slide from scratch, and prints a
confident label with nothing attached. A human who runs only the second command
has no way to know. The warning existed, was printed to a terminal, and died there.

### tissue_analyzer_mcp

```bash
$ python3 tools/analyze_tissue.py --slide data/case_003.pgm --out results/c3.json
{
  "n_tiles_tissue": 82,
  "damage_fraction": 0.451,
  "hard_edge_rate": 0.11,
  "confidence": 0.55,
  "low_confidence": true,
  "usable": true,
  "notes": "elevated edge rate - possible fold or tear"
}

$ python3 tools/classify_tissue.py --features results/c3.json
{
  "label": "necrosis",
  "probability": 0.935,
  "upstream_low_confidence": true,
  "upstream_notes": "elevated edge rate - possible fold or tear",
  "model_card": "clean slides only; folds, tears and pen marks excluded"
}
```

Same numbers. But the second tool takes the **measurement** rather than the
slide, so the warning cannot be dropped on the way in — and it passes it
through. `probability: 0.935` and `upstream_low_confidence: true` now sit in the
same object, where nobody can read one without the other.

---

## Line by line

Both packages now take the same kind of command line, with the same flags and a
config file behind them. That is deliberate: it removes the easy differences so
the real ones stand out.

| | `tissue_analyzer` | `tissue_analyzer_mcp` |
|---|---|---|
| **Arguments** | `--slide --magnification --threshold --out`, config file for defaults | the same | 
| **Type checking** | argparse rejects `20x` | schema rejects `"20x"` before the process even starts |
| **Range checking** | **none** — see below | `50` refused: *"must be ≤ 1 — did you mean 0.5?"* |
| **Output** | a table; `--out x.json` gives flat numbers | JSON with `confidence`, `low_confidence`, `usable`, `notes` |
| **Uncertainty** | a `Note:` line on screen, lost between steps | fields that travel with the answer |
| **Documentation** | `README.md`, read once by a person | `skills/*/SKILL.md`, read by the model every time it uses that tool |
| **Discovery** | you read the README to learn the flags | the server announces its tools and their schemas |
| **Stopping rules** | in the README's prose, and in your head | `agents/tissue-analyst.md` — applied on every run |
| **Who can run it** | you, at a terminal | you, an agent, a web app, another lab's client |

---

## What a good command line still does not give you

`tissue_analyzer` now has a perfectly respectable CLI. Run the three mistakes
from the lecture against it:

**1 · `--magnification 20x`** — caught. argparse knows it wants an integer.

```
analyze_tissue.py: error: argument --magnification: invalid int value: '20x'
```

**2 · `--mag 20`** — caught, but only because the script sets `allow_abbrev=False`.

This one is worth pausing on. **By default, argparse accepts any unambiguous
abbreviation**, so `--mag 20` would have been silently accepted as
`--magnification 20`. It happens to mean the right thing today — and it will
stop meaning the right thing the moment someone adds a `--magnitude` flag. One
line turns a quiet convenience into a loud error:

```python
argparse.ArgumentParser(..., allow_abbrev=False)
```

**3 · `--threshold 50`** — **not caught.**

```
$ python scripts/analyze_tissue.py --slide data/case_003.pgm --threshold 50 --out r.json

  Threshold:                 50.00
  Damage fraction:           100.0%

$ cat r.json
  {"damage_fraction": 1.0, "threshold": 50.0, ...}

$ echo $?
0
```

Exit code zero. A clean JSON file. Every tile counted as damaged, because every
grey value is below 50×255. **100% necrosis, reported with no error anywhere.**

argparse checked the *type* and was satisfied: 50 is a perfectly good float. It
has no idea the number means a fraction. Nothing in a type system can know that
— only the person who wrote the tool knows, and in this package they never wrote
it down.

The MCP package writes it down, in one line of schema:

```json
"damage_threshold_fraction": {"type": "number", "minimum": 0, "maximum": 1}
```

```
argument validation failed (nothing was run):
- 'damage_threshold_fraction' must be <= 1, got 50 (did you mean 0.5?)
```

**This is the entire difference, in one example.** Not "one package is modern and
one is old". Both have a decent CLI. One of them records what its numbers *mean*
in a place a machine can check, and the other keeps that knowledge in the head
of whoever wrote it.

---

## What did NOT change

- `models/tissue_rf_v2.json` — byte-identical
- `data/*.pgm` — byte-identical
- `common.py` — the tile arithmetic is byte-identical
- the numbers

This is the sentence worth saying out loud: **nobody improved the science.** The
second package is the first one with its assumptions written down where a machine
can read them.

---

## And the honest part

`tissue_analyzer/` is a perfectly good research package — a real CLI, a config
file, a model card, a batch script. If you are the only person who runs it, you
know the threshold is a fraction, you remember to check the edge rate, and an
argparse error tells you when you typed something impossible. It is fine, and
better than most published tools.

It stops being fine at exactly three moments:

1. **Someone else runs it** — a new student, a collaborator — and does not carry
   your context.
2. **You run it a hundred times** and stop reading every `Note:` line.
3. **Something automates it** — an agent, a pipeline, a web app — which has no
   eyes, cannot ask you a question, and cannot tell a confident right answer from
   a confident wrong one.

The MCP package is what the first one becomes when any of those three happen. You
are not writing it for the machine. You are writing down what you already know,
in a place it survives.
