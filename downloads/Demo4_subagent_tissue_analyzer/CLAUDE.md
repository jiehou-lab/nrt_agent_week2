# Tissue Analyzer MCP — Scoped Subagent Demo

Delegate complete tissue-analysis requests to the `tissue-analyst` subagent.

The subagent is intentionally restricted to two MCP tools:

- `mcp__tissue-analyzer__analyze_tissue`
- `mcp__tissue-analyzer__classify_tissue`

It does not receive Bash, Read, Write, or Glob.

This package demonstrates **subagent tool scoping**, which is conceptually
separate from project-wide permission rules.
