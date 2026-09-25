#!/usr/bin/env python3
"""
analyze_tissue.py - quantify tissue damage on a whole-slide image

Parameters may be given on the command line, or taken from a config file, or
both: command-line values override the config file, which overrides the
built-in defaults.

Examples:


    # everything explicit
    python scripts/analyze_tissue.py \
        --slide data/case_003.pgm \
        --magnification 20 \
        --threshold 0.45 \
        --out results/case_003.json

    # config file only (config/analysis.yaml)
    python scripts/analyze_tissue.py --slide data/case_003.pgm

    # a different config for a different scanner
    python scripts/analyze_tissue.py --slide s1.pgm --config config/aperio.yaml

Hou Lab, Michigan State University
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_config, read_pgm, tile_stats

DEFAULT_CONFIG = os.path.join("config", "analysis.yaml")
BUILTIN = {"magnification": 20, "damage_threshold": 0.45,
           "min_tiles": 40, "edge_spread_cutoff": 140}


def parse_args():
    p = argparse.ArgumentParser(
        description="Quantify damaged tissue on a whole-slide image.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Command-line values override the config file.",
        # argparse accepts unambiguous abbreviations by default, so '--mag'
        # would silently be taken as '--magnification'. Turn that off: a
        # half-remembered flag should fail loudly, not quietly work.
        allow_abbrev=False)
    p.add_argument("--slide", required=True,
                   help="path to the slide image")
    p.add_argument("--magnification", type=int,
                   help="10, 20 or 40 (default: from config, or 20)")
    p.add_argument("--threshold", type=float,
                   help="grey fraction below which a tile counts as damaged "
                        "(default: from config, or 0.45)")
    p.add_argument("--min-tiles", type=int,
                   help="warn below this many tissue tiles (default: 40)")
    p.add_argument("--config", default=DEFAULT_CONFIG,
                   help="parameter file (default: %s)" % DEFAULT_CONFIG)
    p.add_argument("--out",
                   help="write results here; .json writes JSON, anything else "
                        "writes the text summary")
    p.add_argument("--quiet", action="store_true",
                   help="suppress the printed summary")
    return p.parse_args()


def resolve(args):
    """built-in defaults < config file < command line"""
    cfg = dict(BUILTIN)
    if os.path.exists(args.config):
        cfg.update(load_config(args.config))
    if args.magnification is not None:
        cfg["magnification"] = args.magnification
    if args.threshold is not None:
        cfg["damage_threshold"] = args.threshold
    if args.min_tiles is not None:
        cfg["min_tiles"] = args.min_tiles
    return cfg


def main():
    args = parse_args()
    cfg = resolve(args)

    w, h, px = read_pgm(args.slide)
    n_tissue, n_damaged, n_edges = tile_stats(
        w, h, px, cfg["magnification"], cfg["damage_threshold"],
        cfg["edge_spread_cutoff"])

    frac = n_damaged / n_tissue
    edge_rate = n_edges / n_tissue

    if not args.quiet:
        print("=" * 52)
        print("  Tissue Damage Analysis")
        print("  Slide: " + os.path.basename(args.slide))
        print("=" * 52)
        print("  Magnification:             %dx" % cfg["magnification"])
        print("  Threshold:                 %.2f" % cfg["damage_threshold"])
        print("  Tissue tiles analysed:     %d" % n_tissue)
        print("  Damaged tiles:             %d" % n_damaged)
        print("  Damage fraction:           %.1f%%" % (frac * 100))
        print("  Hard edge rate:            %.1f%%" % (edge_rate * 100))
        print("=" * 52)
        if n_tissue < cfg["min_tiles"]:
            print("  Note: fewer than %d tiles - estimate may be unstable"
                  % cfg["min_tiles"])
        if edge_rate > 0.08:
            print("  Note: elevated edge rate - check slide for folds")
        print()

    if args.out:
        d = os.path.dirname(args.out)
        if d:
            os.makedirs(d, exist_ok=True)
        if args.out.endswith(".json"):
            json.dump({"slide": os.path.basename(args.slide),
                       "magnification": cfg["magnification"],
                       "threshold": cfg["damage_threshold"],
                       "tissue_tiles": n_tissue,
                       "damaged_tiles": n_damaged,
                       "damage_fraction": round(frac, 3),
                       "edge_rate": round(edge_rate, 3)},
                      open(args.out, "w"), indent=2)
        else:
            with open(args.out, "w") as f:
                f.write("slide: %s\nmagnification: %d\ntissue_tiles: %d\n"
                        "damage_fraction: %.1f%%\nedge_rate: %.1f%%\n"
                        % (os.path.basename(args.slide), cfg["magnification"],
                           n_tissue, frac * 100, edge_rate * 100))
        if not args.quiet:
            print("  Saved to %s" % args.out)


if __name__ == "__main__":
    main()
