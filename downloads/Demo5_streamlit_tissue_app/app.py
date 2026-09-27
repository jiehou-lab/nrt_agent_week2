#!/usr/bin/env python3
"""Demo 5 — the same analysis reached two ways.

Path A  button        -> MCP tool            -> result      (no language model)
Path B  free text     -> Claude Code -> MCP tool -> result  (a model interprets)

Both paths end at the same server.py and return the same numbers. The point of
this app is to make the difference between them visible, so you can decide which
parts of your own interface actually need a model.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import streamlit as st

from mcp_client import MCPClient
from stream_parse import parse_lines, summarise

ROOT = Path(__file__).resolve().parent
SLIDES = sorted(p.name for p in (ROOT / "data").glob("*.pgm"))

st.set_page_config(page_title="Tissue analyzer — two paths", layout="wide")


# ----------------------------------------------------------------- helpers
def parse_json_block(text):
    """Tool output is JSON; return it as a dict, or None if it is an error string."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def show_measurement(d):
    if not d:
        return
    cols = st.columns(4)
    cols[0].metric("Damage fraction", d.get("damage_fraction"))
    cols[1].metric("Hard edge rate", d.get("hard_edge_rate"))
    cols[2].metric("Confidence", d.get("confidence"))
    cols[3].metric("Usable", str(d.get("usable")))
    if d.get("low_confidence"):
        st.warning("low_confidence is true — notes: %s" % d.get("notes", ""))


def claude_available():
    return shutil.which("claude") is not None



KEYS = ("damage_fraction", "hard_edge_rate", "confidence", "usable")


def request_from_steps(steps):
    """The arguments the model actually sent, dug out of a trace's tool calls."""
    for st in steps or []:
        if st.get("kind") == "tool_use" and "analyze" in st.get("name", ""):
            return st.get("input", {}) or {}
    return {}


def measurement_from_steps(steps):
    """The analyze_tissue numbers, dug out of a trace's tool results."""
    for st in steps or []:
        if st.get("kind") != "tool_result":
            continue
        d = parse_json_block(st.get("text", ""))
        if isinstance(d, dict) and "damage_fraction" in d:
            return d
    return None


def render_steps(steps, container):
    """Draw a trace as a list of steps. The tool calls are the evidence."""
    n = 0
    for st in steps:
        kind = st["kind"]
        if kind == "text":
            container.markdown("> " + st["text"].replace("\n", "\n> "))
        elif kind == "tool_use":
            n += 1
            container.markdown("**%d. calls `%s`**" % (n, st["name"]))
            container.code(json.dumps(st.get("input", {}), indent=2), language="json")
        elif kind == "tool_result":
            label = "returns an error" if st.get("is_error") else "gets back"
            container.markdown("&nbsp;&nbsp;&nbsp;↳ *%s*" % label, unsafe_allow_html=True)
            container.code((st.get("text") or "")[:2000], language="json")
        elif kind == "result":
            container.markdown("---")
            container.markdown(st.get("text") or "")
        else:
            with container.expander("unrecognised event"):
                container.json(st.get("raw"))


def run_streaming(cmd, container):
    """Run Claude Code and draw each step as it arrives. Returns (steps, code, stderr)."""
    steps, lines = [], []
    proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1,
                            env=os.environ.copy())
    for line in proc.stdout:
        lines.append(line)
        for st in parse_lines([line]):
            steps.append(st)
            render_steps([st], container)
    proc.wait(timeout=300)
    return steps, proc.returncode, proc.stderr.read()


# ----------------------------------------------------------------- sidebar
st.sidebar.header("Inputs")
slide = st.sidebar.selectbox("Slide", SLIDES,
                             index=SLIDES.index("case_mild_injury_histology.pgm")
                             if "case_mild_injury_histology.pgm" in SLIDES else 0)
magnification = st.sidebar.selectbox("magnification", [10, 20, 40], index=1)
threshold = st.sidebar.slider("damage_threshold_fraction", 0.0, 1.0, 0.45, 0.01)

preview = ROOT / "previews" / (Path(slide).stem + ".png")
if preview.exists():
    st.sidebar.image(str(preview), caption=slide)

st.sidebar.divider()
st.sidebar.caption("Environment")
st.sidebar.write("MCP server: `server.py` (started per call)")
st.sidebar.write("Claude Code on PATH: **%s**" % ("yes" if claude_available() else "no"))
settings = ROOT / ".claude" / "settings.json"
st.sidebar.write("Pre-approved permissions: **%s**" % ("yes" if settings.exists() else "no"))


# ----------------------------------------------------------------- header
st.title("Tissue analyzer — two paths to the same number")
st.write(
    "Both tabs below run the **same** `analyze_tissue` tool against the **same** slide "
    "with the **same** parameters. Only the route differs."
)
st.code(
    "Path A   button        ->  MCP tool                 ->  result   (no model)\n"
    "Path B   free text     ->  Claude Code -> MCP tool  ->  result   (model interprets)",
    language="text",
)

tab_a, tab_b, tab_c = st.tabs(["Path A — direct tool call",
                               "Path B — ask in English",
                               "Compare"])


# ----------------------------------------------------------------- Path A
with tab_a:
    st.subheader("No language model is involved here")
    st.write(
        "The app already knows which tool to call and what the arguments mean, so it "
        "calls the tool itself. This is an ordinary program with a form on the front."
    )
    args = {"slide": "data/" + slide,
            "magnification": magnification,
            "damage_threshold_fraction": threshold}
    st.caption("Exactly what gets sent over MCP:")
    st.code(json.dumps({"name": "analyze_tissue", "arguments": args}, indent=2), language="json")

    if st.button("Run analyze_tissue", type="primary", key="run_direct"):
        with MCPClient() as c:
            text, err = c.call("analyze_tissue", args)
        st.session_state["a_text"] = text
        st.session_state["a_err"] = err

    if "a_text" in st.session_state:
        if st.session_state["a_err"]:
            st.error("The server refused the call — nothing ran.")
            st.code(st.session_state["a_text"], language="text")
            st.caption(
                "That refusal came from the schema in server.py, not from a model. "
                "Try setting the threshold to 1.00 and then editing it to 50 in the code "
                "to see the range check fire."
            )
        else:
            d = parse_json_block(st.session_state["a_text"])
            show_measurement(d)
            with st.expander("Raw structured result"):
                st.json(d if d else st.session_state["a_text"])

            if d and st.button("Then classify it", key="run_classify"):
                out = ROOT / "results" / (Path(slide).stem + "_analyze.json")
                out.parent.mkdir(exist_ok=True)
                out.write_text(json.dumps(d, indent=2))
                with MCPClient() as c:
                    ctext, cerr = c.call("classify_tissue", {"features": str(out.relative_to(ROOT))})
                cd = parse_json_block(ctext)
                if cd:
                    st.success("%s  (probability %s)" % (cd.get("label"), cd.get("probability")))
                    st.json(cd)
                    if d.get("low_confidence"):
                        st.error(
                            "Note what just happened: the measurement flagged "
                            "low_confidence, and the classification above does not mention "
                            "it at all. The label is the same one a genuinely mild slide gets."
                        )
                else:
                    st.code(ctext, language="text")


# ----------------------------------------------------------------- Path B
with tab_b:
    st.subheader("A model reads the request and chooses the call")
    st.write(
        "Here the app does not know what you want. It hands your sentence to Claude Code, "
        "which is running in this project folder, so it can see `.mcp.json` and the tool "
        "schemas and decide what to call."
    )
    prompt = st.text_area(
        "Ask for an analysis in your own words",
        "Analyze data/%s at %dx magnification with a %d%% damage threshold, "
        "then tell me whether the slide is usable." % (slide, magnification, int(threshold * 100)),
        height=110,
    )
    show_steps = st.checkbox(
        "Show Claude's steps as they happen (tool calls and results, not just the answer)",
        value=False,
        help="Uses --output-format stream-json, which emits one JSON event per line. "
             "Tick this to see the tool calls rather than only the final answer.")
    cmd = (["claude", "-p", prompt, "--output-format", "stream-json", "--verbose"]
           if show_steps else ["claude", "-p", prompt, "--output-format", "json"])
    st.caption("The command this app runs (note the working directory):")
    st.code("cd %s\n%s" % (ROOT.name, " ".join(
        [c if " " not in c else '"%s"' % c for c in cmd])), language="bash")
    st.caption("Shown relative to where you unzipped it; the app runs it with the full path.")

    if not claude_available():
        st.warning(
            "`claude` is not on this app's PATH, so Path B cannot run. The Streamlit "
            "process inherits the shell it was started from — launch the app from a "
            "terminal where `claude --version` works."
        )
    elif st.button("Send to Claude Code", type="primary", key="run_agent"):
        st.session_state.pop("b_steps", None)
        if show_steps:
            st.markdown("#### What it actually did")
            box = st.container()
            try:
                steps, code, err = run_streaming(cmd, box)
                st.session_state["b_steps"] = steps
                st.session_state["b_code"] = code
                st.session_state["b_err"] = err
                st.session_state["b_out"] = ""
                if not steps:
                    st.warning(
                        "No steps came back. Your version of Claude Code may not support "
                        "`--output-format stream-json`; untick the box above to use the "
                        "plain JSON output instead.")
            except Exception as exc:                      # noqa: BLE001
                st.session_state["b_code"] = -1
                st.session_state["b_err"] = str(exc)
                st.session_state["b_out"] = ""
        else:
            with st.spinner("Claude Code is working (this takes longer than Path A)…"):
                try:
                    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True,
                                       text=True, timeout=300, env=os.environ.copy())
                    st.session_state["b_out"] = p.stdout
                    st.session_state["b_err"] = p.stderr
                    st.session_state["b_code"] = p.returncode
                except subprocess.TimeoutExpired:
                    st.session_state["b_out"] = ""
                    st.session_state["b_err"] = "timed out after 300s"
                    st.session_state["b_code"] = -1

    sample = ROOT / "docs" / "sample_trace.jsonl"
    if sample.exists():
        with st.expander("Replay a saved trace (no tokens, no Claude Code needed)"):
            st.write("A recorded run on the fold-artifact slide, so you can see the shape of "
                     "a trace before spending anything on your own.")
            if st.button("Replay", key="replay_sample"):
                st.session_state["b_steps"] = list(parse_lines(sample.read_text().splitlines()))
                st.session_state["b_code"] = 0
                st.session_state["b_err"] = ""
                st.session_state["b_out"] = ""

    if st.session_state.get("b_steps"):
        s_sum = summarise(st.session_state["b_steps"])
        st.info("%d steps · %d tool call(s): %s" % (
            s_sum["n_steps"], s_sum["n_tool_calls"], ", ".join(s_sum["tools"]) or "none"))
        with st.expander("The trace, step by step", expanded=True):
            render_steps(st.session_state["b_steps"], st)
        st.caption(
            "This is the part worth reading. The prose is what Claude says it did; the tool "
            "calls above are what it did. When those two disagree, the tool calls are right.")

    if "b_out" in st.session_state:
        if st.session_state["b_code"] != 0:
            st.error("Claude Code exited with code %s" % st.session_state["b_code"])
        payload = parse_json_block(st.session_state["b_out"])
        if payload:
            st.markdown(payload.get("result") or payload.get("text") or "")
            with st.expander("Full JSON from Claude Code"):
                st.json(payload)
        else:
            st.code(st.session_state["b_out"] or "(no output)", language="text")
        if st.session_state.get("b_err"):
            with st.expander("stderr"):
                st.code(st.session_state["b_err"], language="text")
        st.caption(
            "If nothing ran, check `.claude/settings.json`. In `-p` mode Claude Code "
            "cannot stop and ask you for permission, so any tool that is not already "
            "allowed is simply not used."
        )


# ----------------------------------------------------------------- Compare
with tab_c:
    st.subheader("Same numbers, different routes")
    a = parse_json_block(st.session_state.get("a_text", "")) or {}
    left, right = st.columns(2)
    with left:
        st.markdown("**Path A — direct call**")
        if a:
            st.json({k: a.get(k) for k in
                     ("damage_fraction", "hard_edge_rate", "confidence", "usable")})
        else:
            st.info("Run Path A first.")
        st.markdown(
            "- deterministic: identical input, identical output\n"
            "- fast, and free\n"
            "- cannot handle a request the form does not already cover"
        )
    b = measurement_from_steps(st.session_state.get("b_steps"))
    if b is None and st.session_state.get("b_out"):
        b = parse_json_block(st.session_state["b_out"]) or {}
        b = b if "damage_fraction" in b else None

    with right:
        st.markdown("**Path B — through the model**")
        if b:
            st.json({k: b.get(k) for k in KEYS})
        elif st.session_state.get("b_steps") or st.session_state.get("b_out"):
            st.warning("Path B ran, but no measurement came back in the trace.")
        else:
            st.info("Run Path B first.")
        st.markdown(
            "- handles wording the form has no field for\n"
            "- can chain steps and explain what it saw\n"
            "- slower, costs tokens, and may vary between runs"
        )

    if a and b:
        same = all(a.get(k) == b.get(k) for k in KEYS)
        if same:
            st.success(
                "Identical values from both routes. The model varied the wording, not the "
                "measurement — because the measurement came from a tool with a schema."
            )
        else:
            sent = request_from_steps(st.session_state.get("b_steps"))
            asked = {"slide": "data/" + slide, "magnification": magnification,
                     "damage_threshold_fraction": threshold}
            mismatched = [k for k in asked if k in sent and sent[k] != asked[k]]
            if mismatched:
                st.warning(
                    "The two routes disagree, and the trace says why: Path B was run with "
                    + ", ".join("`%s` = %r (the form has %r)" % (k, sent[k], asked[k])
                                for k in mismatched)
                    + ". Set the sidebar to match, or re-run Path A, before comparing."
                )
            else:
                st.warning(
                    "The two routes disagree. Read the arguments in the Path B trace — that is "
                    "where the difference will be."
                )
        diff = {k: {"A": a.get(k), "B": b.get(k)} for k in KEYS}
        with st.expander("Field by field"):
            st.json(diff)

    if st.session_state.get("b_out"):
        with st.expander("Path B — the full reply from Claude Code"):
            payload = parse_json_block(st.session_state["b_out"])
            if payload:
                st.json(payload)
            else:
                st.code(st.session_state["b_out"][:4000], language="text")

    st.divider()
    st.markdown(
        "#### The question to take to your own project\n"
        "Every control in an interface is a decision about **who interprets the request**. "
        "A button means you already decided. A text box means the model decides. "
        "Most research applications want both, and putting a model behind a button that "
        "always does the same thing adds latency, cost and variance while buying nothing."
    )
