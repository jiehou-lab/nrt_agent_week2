# Tissue analyzer — Streamlit front end

This project is called two ways: by a Streamlit app that talks to the MCP server
directly, and by you, through `claude -p` started in this folder.

## Preferred workflow

Use the `tissue-analyzer` MCP tools. Do not read `.pgm` files and do not invoke
the Python scripts in `tools/` yourself.

1. `analyze_tissue` first, with an explicit `out` path under `results/`.
2. `classify_tissue` on that saved JSON, only if the measurement was usable.

## Reporting rule

Report `damage_fraction`, `hard_edge_rate`, `confidence` and `usable` exactly as
the tool returned them. **If `low_confidence` is true, say so in your first
sentence** — a label alone is not a usable answer for a slide the measurement
was unsure about.

## Non-interactive use

This project is frequently run with `claude -p` from a web app, where nothing can
answer a permission prompt. `.claude/settings.json` pre-approves the two MCP
tools for that reason. If you find yourself wanting a tool that is not allowed,
say so in your answer instead of failing silently.
