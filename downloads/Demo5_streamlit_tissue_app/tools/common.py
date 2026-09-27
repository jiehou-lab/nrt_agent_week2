"""Shared helpers for the analysis scripts."""
import os

CONFIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "config", "analysis.yaml")


def load_config(path=CONFIG):
    """Minimal YAML reader - the file only has scalars."""
    cfg = {}
    for line in open(path):
        line = line.split("#")[0].strip()
        if not line or ":" not in line:
            continue
        k, v = [s.strip() for s in line.split(":", 1)]
        try:
            cfg[k] = int(v) if v.isdigit() else float(v)
        except ValueError:
            cfg[k] = v
    return cfg


def read_pgm(path):
    toks = []
    for line in open(path):
        if not line.startswith("#"):
            toks += line.split()
    w, h = int(toks[1]), int(toks[2])
    return w, h, [int(v) for v in toks[4:4 + w * h]]


def tile_stats(w, h, px, mag, threshold, edge_cutoff):
    size = {10: 16, 20: 8, 40: 4}[mag]
    cut = threshold * 255
    n_tissue = n_damaged = n_edges = 0
    for ty in range(0, h - size + 1, size):
        for tx in range(0, w - size + 1, size):
            vals = [px[(ty + dy) * w + tx + dx]
                    for dy in range(size) for dx in range(size)]
            if max(vals) >= 230:
                continue
            n_tissue += 1
            if sum(vals) / len(vals) < cut:
                n_damaged += 1
            if max(vals) - min(vals) > edge_cutoff:
                n_edges += 1
    return n_tissue, n_damaged, n_edges
