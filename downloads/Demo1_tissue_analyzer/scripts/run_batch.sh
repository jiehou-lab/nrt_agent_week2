#!/usr/bin/env bash
# Run the analysis over every slide in data/
for f in data/*.pgm; do
    echo "Processing $f"
    python3 scripts/analyze_tissue.py --slide "$f" \
            --out "results/$(basename "${f%.*}")_analysis.txt"
done
