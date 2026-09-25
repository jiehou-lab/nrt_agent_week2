#!/usr/bin/env python3
"""Quantify tissue damage on a slide.  Same maths as the original package.

What changed: the parameters are arguments instead of a config file, every one
is validated before anything runs, and the result is JSON that carries how much
the tool trusts its own answer.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_pgm, tile_stats

MIN_TILES = 40
EDGE_CUTOFF = 140


def die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(2)


p = argparse.ArgumentParser(description="Quantify damaged tissue on a slide.")
p.add_argument("--slide", required=True)
p.add_argument("--magnification", type=int, choices=[10, 20, 40], default=20,
               help="a bare integer, not '20x'")
p.add_argument("--damage-threshold-fraction", type=float, default=0.45,
               help="a fraction between 0 and 1, not a percentage")
p.add_argument("--out")
a = p.parse_args()

if not 0 <= a.damage_threshold_fraction <= 1:
    die("--damage-threshold-fraction must be between 0 and 1 (got %r); "
        "if you meant a percentage, use %.2f"
        % (a.damage_threshold_fraction, a.damage_threshold_fraction / 100))
if not os.path.exists(a.slide):
    die("slide not found: %s" % a.slide)

w, h, px = read_pgm(a.slide)
n_tissue, n_damaged, n_edges = tile_stats(
    w, h, px, a.magnification, a.damage_threshold_fraction, EDGE_CUTOFF)
if n_tissue == 0:
    die("no tissue detected on this slide")

frac = n_damaged / n_tissue
edge_rate = n_edges / n_tissue

# the tool's own view of how far to trust the number it just produced
conf = 0.95
if n_tissue < MIN_TILES:
    conf -= 0.50
if edge_rate > 0.08:
    conf -= 0.40
conf = round(max(0.05, conf), 2)

res = {
    "tool": "analyze_tissue",
    "slide": a.slide,
    "magnification": a.magnification,
    "damage_threshold_fraction": a.damage_threshold_fraction,
    "n_tiles_tissue": n_tissue,
    "n_tiles_damaged": n_damaged,
    "damage_fraction": round(frac, 3),
    "hard_edge_rate": round(edge_rate, 3),
    "confidence": conf,
    "low_confidence": conf < 0.6,
    "usable": n_tissue >= MIN_TILES,
    "notes": ("fewer than %d tiles - estimate unstable" % MIN_TILES if n_tissue < MIN_TILES
              else "elevated edge rate - possible fold or tear" if edge_rate > 0.08
              else "ok"),
}
out = json.dumps(res, indent=2)
print(out)
if a.out:
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    open(a.out, "w").write(out + "\n")
