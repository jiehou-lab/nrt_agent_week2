#!/usr/bin/env python3
"""Minimal MCP stdio client.

Starts server.py as a subprocess, speaks JSON-RPC over its stdin/stdout, and
returns the text a tool produced. This is the same three messages Claude Code
sends: initialize, tools/list, tools/call.

Nothing here is Streamlit-specific — you can import it from any Python program.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class MCPClient:
    def __init__(self, command=None):
        self.command = command or [sys.executable, str(ROOT / "server.py")]
        self.proc = None
        self._id = 0

    def __enter__(self):
        self.proc = subprocess.Popen(
            self.command, cwd=str(ROOT),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,
        )
        self._rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "demo5-streamlit", "version": "1.0.0"},
        })
        return self

    def __exit__(self, *exc):
        if self.proc:
            try:
                self.proc.stdin.close()
            except Exception:
                pass
            self.proc.terminate()
            self.proc.wait(timeout=5)

    def _rpc(self, method, params=None):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}}
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("MCP server closed the connection")
            line = line.strip()
            if not line:
                continue
            reply = json.loads(line)
            if reply.get("id") == self._id:
                return reply

    def list_tools(self):
        return self._rpc("tools/list")["result"]["tools"]

    def call(self, name, arguments):
        """Return (text, is_error). The text is exactly what the server returned."""
        reply = self._rpc("tools/call", {"name": name, "arguments": arguments})
        result = reply.get("result", {})
        text = "\n".join(c.get("text", "") for c in result.get("content", []))
        return text, bool(result.get("isError"))


if __name__ == "__main__":
    with MCPClient() as c:
        for t in c.list_tools():
            print(t["name"], "-", t["description"][:70])
        text, err = c.call("analyze_tissue", {
            "slide": "data/case_mild_injury_histology.pgm",
            "magnification": 20,
            "damage_threshold_fraction": 0.45,
        })
        print("\nisError:", err)
        print(text)
