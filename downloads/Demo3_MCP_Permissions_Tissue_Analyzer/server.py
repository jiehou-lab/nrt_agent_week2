#!/usr/bin/env python3
"""MCP server for tissue_analyzer — standard library only, no pip install.

It does three things: say what it is, list its tools with a JSON schema each,
and run one when asked. Every argument is checked against the schema BEFORE the
underlying script is started.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TOOLS = [
    {
        "name": "analyze_tissue",
        "description": ("Measure damaged tissue on a slide. Run this FIRST. Reads the image "
                        "locally and returns numbers only, with its own confidence."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "slide": {"type": "string", "description": "path to a slide, e.g. data/case_003.pgm"},
                "magnification": {"type": "integer", "enum": [10, 20, 40], "default": 20},
                "damage_threshold_fraction": {
                    "type": "number", "minimum": 0, "maximum": 1, "default": 0.45,
                    "description": "a FRACTION between 0 and 1, never a percentage"},
                "out": {"type": "string"},
            },
            "required": ["slide"],
        },
        "script": "tools/analyze_tissue.py",
        "flags": {"slide": "--slide", "magnification": "--magnification",
                  "damage_threshold_fraction": "--damage-threshold-fraction", "out": "--out"},
    },
    {
        "name": "classify_tissue",
        "description": ("Label a slide normal / mild_injury / necrosis from analyze_tissue "
                        "output. Trained on clean slides only — no artifact class, so it "
                        "answers confidently even on an unusable slide."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "features": {"type": "string", "description": "the JSON from analyze_tissue"},
                "out": {"type": "string"},
            },
            "required": ["features"],
        },
        "script": "tools/classify_tissue.py",
        "flags": {"features": "--features", "out": "--out"},
    },
]
BY_NAME = {t["name"]: t for t in TOOLS}


def validate(schema, args):
    errs, props = [], schema.get("properties", {})
    for k in schema.get("required", []):
        if k not in args:
            errs.append("missing required argument '%s'" % k)
    for k, v in args.items():
        if k not in props:
            errs.append("unknown argument '%s' (allowed: %s)" % (k, ", ".join(props)))
            continue
        s = props[k]
        if s.get("type") == "integer" and not isinstance(v, int):
            errs.append("'%s' must be an integer, got %r" % (k, v))
        if s.get("type") == "number" and not isinstance(v, (int, float)):
            errs.append("'%s' must be a number, got %r" % (k, v))
        if "enum" in s and v not in s["enum"]:
            errs.append("'%s' must be one of %s, got %r" % (k, s["enum"], v))
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if "minimum" in s and v < s["minimum"]:
                errs.append("'%s' must be >= %s, got %s" % (k, s["minimum"], v))
            if "maximum" in s and v > s["maximum"]:
                hint = " (did you mean %g?)" % (v / 100) if s["maximum"] == 1 else ""
                errs.append("'%s' must be <= %s, got %s%s" % (k, s["maximum"], v, hint))
    return errs


def call(name, args):
    spec = BY_NAME.get(name)
    if not spec:
        return "unknown tool: %s" % name, True
    errs = validate(spec["inputSchema"], args)
    if errs:
        return "argument validation failed (nothing was run):\n- " + "\n- ".join(errs), True
    cmd = [sys.executable, str(ROOT / spec["script"])]
    for k, v in args.items():
        cmd += [spec["flags"][k], str(v)]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr else ""), p.returncode != 0


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        mid, method = msg.get("id"), msg.get("method")
        if method == "initialize":
            ver = (msg.get("params") or {}).get("protocolVersion") or "2024-11-05"
            res = {"protocolVersion": ver, "capabilities": {"tools": {}},
                   "serverInfo": {"name": "tissue-analyzer", "version": "2.0.0"}}
        elif method == "tools/list":
            res = {"tools": [{k: t[k] for k in ("name", "description", "inputSchema")}
                             for t in TOOLS]}
        elif method == "tools/call":
            pr = msg.get("params") or {}
            text, err = call(pr.get("name"), pr.get("arguments") or {})
            res = {"content": [{"type": "text", "text": text}], "isError": err}
        elif mid is None:
            continue
        else:
            print(json.dumps({"jsonrpc": "2.0", "id": mid,
                              "error": {"code": -32601, "message": "no method " + str(method)}}),
                  flush=True)
            continue
        if mid is not None:
            print(json.dumps({"jsonrpc": "2.0", "id": mid, "result": res}), flush=True)


if __name__ == "__main__":
    main()
