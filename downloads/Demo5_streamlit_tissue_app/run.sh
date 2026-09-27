#!/usr/bin/env bash
# Start the app from THIS folder so that Claude Code (Path B) and the MCP server
# both resolve .mcp.json, CLAUDE.md and data/ correctly.
cd "$(dirname "$0")"
exec streamlit run app.py
