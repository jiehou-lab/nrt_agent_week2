#!/usr/bin/env python3
"""Turn Claude Code's streaming output into a list of steps we can draw.

`claude -p --output-format stream-json --verbose` emits one JSON object per
line. The exact shape has changed across versions, so this parser is written to
be forgiving: it looks for the things it recognises and labels everything else
`unknown` rather than throwing. A trace that renders imperfectly is far better
than an app that crashes on an unfamiliar event.

Every step is a plain dict:

    {"kind": "text",        "text": ...}
    {"kind": "tool_use",    "name": ..., "input": {...}}
    {"kind": "tool_result", "text": ..., "is_error": bool}
    {"kind": "result",      "text": ..., "raw": {...}}
    {"kind": "unknown",     "raw": {...}}
"""
import json


def _blocks(msg):
    """Content blocks out of an Anthropic-style message, whatever the nesting."""
    if not isinstance(msg, dict):
        return []
    content = msg.get("content")
    if content is None and isinstance(msg.get("message"), dict):
        content = msg["message"].get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return content if isinstance(content, list) else []


def parse_event(obj):
    """One JSON object -> zero or more steps."""
    steps = []
    if not isinstance(obj, dict):
        return [{"kind": "unknown", "raw": obj}]

    etype = obj.get("type")

    # the final summary object
    if etype == "result":
        steps.append({"kind": "result",
                      "text": obj.get("result") or obj.get("text") or "",
                      "raw": obj})
        return steps

    # assistant / user turns carry the interesting blocks
    for b in _blocks(obj) or _blocks(obj.get("message")):
        if not isinstance(b, dict):
            continue
        bt = b.get("type")
        if bt == "text" and b.get("text", "").strip():
            steps.append({"kind": "text", "text": b["text"]})
        elif bt == "tool_use":
            steps.append({"kind": "tool_use",
                          "name": b.get("name", "?"),
                          "input": b.get("input", {})})
        elif bt == "tool_result":
            c = b.get("content")
            if isinstance(c, list):
                c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
            steps.append({"kind": "tool_result",
                          "text": c if isinstance(c, str) else json.dumps(c, indent=2),
                          "is_error": bool(b.get("is_error"))})
        elif bt == "thinking" and b.get("thinking"):
            steps.append({"kind": "text", "text": b["thinking"]})

    if not steps and etype not in ("system", "stream_event", None):
        steps.append({"kind": "unknown", "raw": obj})
    return steps


def parse_lines(lines):
    """Iterate steps from newline-delimited JSON. Bad lines are skipped."""
    for line in lines:
        line = (line or "").strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        for step in parse_event(obj):
            yield step


def summarise(steps):
    calls = [s for s in steps if s["kind"] == "tool_use"]
    errors = [s for s in steps if s["kind"] == "tool_result" and s.get("is_error")]
    return {"n_steps": len(steps), "n_tool_calls": len(calls),
            "tools": [c["name"] for c in calls], "n_errors": len(errors)}
