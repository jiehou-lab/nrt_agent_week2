# Tissue Analyzer MCP — Permission Demo

This project demonstrates a permission layer added on top of the MCP version.

## Preferred workflow

For tissue analysis, use the `tissue-analyzer` MCP tools instead of reading raw
`.pgm` files or invoking the Python tools directly.

Use:
- `analyze_tissue`
- `classify_tissue`

For chaining:
1. call `analyze_tissue` with an explicit `out` path;
2. pass that saved JSON path to `classify_tissue`.

## Data-access rule

Claude Code should not directly inspect or edit files under `data/`.

This is a teaching example of **Claude Code permission rules**. It is not an
operating-system sandbox. The local MCP server still runs with the filesystem
permissions of the user who launched it.
