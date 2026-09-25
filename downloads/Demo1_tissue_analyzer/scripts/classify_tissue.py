#!/usr/bin/env python3
"""
classify_tissue.py - assign a tissue state label using tissue_rf_v2

Examples:

    python scripts/classify_tissue.py --slide data/case_003.pgm
    python scripts/classify_tissue.py --slide s1.pgm --magnification 40

Runs the analysis first, then applies the trained model from models/.
See models/model_card.md for the model's limitations.

Hou Lab, Michigan State University
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_config, read_pgm, tile_stats

DEFAULT_CONFIG = os.path.join("config", "analysis.yaml")


def main():
    p = argparse.ArgumentParser(description="Label tissue state on a slide.",
                                allow_abbrev=False)
    p.add_argument("--slide", required=True)
    p.add_argument("--magnification", type=int)
    p.add_argument("--threshold", type=float)
    p.add_argument("--config", default=DEFAULT_CONFIG)
    p.add_argument("--out")
    a = p.parse_args()

    cfg = load_config(a.config) if os.path.exists(a.config) else {}
    mag = a.magnification if a.magnification is not None else cfg.get("magnification", 20)
    thr = a.threshold if a.threshold is not None else cfg.get("damage_threshold", 0.45)
    model = json.load(open(cfg.get("model_path", "models/tissue_rf_v2.json")))

    w, h, px = read_pgm(a.slide)
    n_tissue, n_damaged, _ = tile_stats(
        w, h, px, mag, thr, cfg.get("edge_spread_cutoff", 140))
    frac = n_damaged / n_tissue

    b, c = model["decision_boundaries"], model["calibration"]
    if frac < b["normal_max"]:
        label, prob = "normal", 0.91 - frac
    elif frac < b["mild_max"]:
        label, prob = "mild_injury", 0.70
    else:
        label, prob = "necrosis", min(c["cap"], c["intercept"] + c["slope"] * frac)

    print()
    print("  Slide:          %s" % os.path.basename(a.slide))
    print("  Damage:         %.1f%%" % (frac * 100))
    print("  Classification: %s (%.1f%% confidence)" % (label.upper(), prob * 100))
    print("  Model:          %s" % model["name"])
    print()

    if a.out:
        d = os.path.dirname(a.out)
        if d:
            os.makedirs(d, exist_ok=True)
        json.dump({"slide": os.path.basename(a.slide),
                   "damage_fraction": round(frac, 3),
                   "label": label, "probability": round(prob, 3),
                   "model": model["name"]}, open(a.out, "w"), indent=2)
        print("  Saved to %s\n" % a.out)


if __name__ == "__main__":
    main()
