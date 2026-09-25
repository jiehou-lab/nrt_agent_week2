#!/usr/bin/env python3
"""Label a slide using tissue_rf_v2.  Same model file as the original package.

What changed: it takes the MEASUREMENT rather than the slide, so the warning the
measurement carried cannot be lost on the way in — and it passes that warning
through to its own output.
"""
import argparse
import json
import os
import sys

MODEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "models", "tissue_rf_v2.json")


def die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(2)


p = argparse.ArgumentParser(description="Label tissue state from a measurement.")
p.add_argument("--features", required=True, help="JSON written by analyze_tissue")
p.add_argument("--out")
a = p.parse_args()

if not os.path.exists(a.features):
    die("features file not found: %s (run analyze_tissue first)" % a.features)
f = json.loads(open(a.features).read())
if "damage_fraction" not in f:
    die("%s has no 'damage_fraction' - is it really analyze_tissue output?" % a.features)

m = json.load(open(MODEL))
b, c = m["decision_boundaries"], m["calibration"]
d = f["damage_fraction"]
if d < b["normal_max"]:
    label, prob = "normal", round(0.91 - d, 3)
elif d < b["mild_max"]:
    label, prob = "mild_injury", 0.70
else:
    label, prob = "necrosis", round(min(c["cap"], c["intercept"] + c["slope"] * d), 3)

res = {
    "tool": "classify_tissue",
    "features_from": a.features,
    "label": label,
    "probability": prob,
    "classes_the_model_knows": m["classes"],
    "model": m["name"],
    "model_card": m["training_notes"],
    # the warning travels with the answer instead of being printed and forgotten
    "upstream_low_confidence": bool(f.get("low_confidence")),
    "upstream_notes": f.get("notes", ""),
}
out = json.dumps(res, indent=2)
print(out)
if a.out:
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    open(a.out, "w").write(out + "\n")
