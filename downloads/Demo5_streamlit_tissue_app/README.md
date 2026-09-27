# Demo 5 — the same analysis reached two ways

A Streamlit front end over the Demo 2 MCP server.

    Path A   a button      ->  MCP tool                  ->  result   (no model)
    Path B   a text box    ->  Claude Code -> MCP tool    ->  result   (a model interprets)

Both end at the same `server.py` and return the same numbers. The app exists to
make the difference visible, so you can decide which parts of your own interface
actually need a model behind them.

## Run it

    python3 -m venv .demo_venv
    source .demo_venv/bin/activate        # Windows: .demo_venv\Scripts\activate
    pip install -r requirements.txt
    ./run.sh                              # or: streamlit run app.py

Start it from a terminal where `claude --version` works, or Path B has no way to
find Claude Code — a GUI process only inherits the environment it was launched
from.

## Files

    app.py                  the Streamlit app, both paths
    mcp_client.py           ~70 lines of JSON-RPC: initialize, tools/list, tools/call
    server.py               the MCP server from Demo 2, unchanged
    CLAUDE.md               how Claude Code should behave in this folder
    .claude/settings.json   pre-approved tools - required for `claude -p`
    tools/ data/ models/    the analysis, unchanged since Demo 1

## The part most people get wrong

In `-p` (non-interactive) mode Claude Code cannot stop and ask permission. A tool
that is not already allowed is simply not used, and you get a confident answer
that skipped the step you wanted. `.claude/settings.json` is what makes Path B
work at all — which is why Demo 3 comes before this one.
