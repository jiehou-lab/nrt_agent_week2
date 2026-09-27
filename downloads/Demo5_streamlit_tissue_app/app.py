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
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    st.caption("The command this app runs (note the working directory):")
    st.code("cd %s\n%s" % (ROOT, " ".join(
        [c if " " not in c else '"%s"' % c for c in cmd])), language="bash")

    if not claude_available():
        st.warning(
            "`claude` is not on this app's PATH, so Path B cannot run. The Streamlit "
            "process inherits the shell it was started from — launch the app from a "
            "terminal where `claude --version` works."
        )
    elif st.button("Send to Claude Code", type="primary", key="run_agent"):
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
    with right:
        st.markdown("**Path B — through the model**")
        if "b_out" in st.session_state:
            st.code((st.session_state["b_out"] or "")[:1200], language="json")
        else:
            st.info("Run Path B first.")
        st.markdown(
            "- handles wording the form has no field for\n"
            "- can chain steps and explain what it saw\n"
            "- slower, costs tokens, and may vary between runs"
        )

    st.divider()
    st.markdown(
        "#### The question to take to your own project\n"
        "Every control in an interface is a decision about **who interprets the request**. "
        "A button means you already decided. A text box means the model decides. "
        "Most research applications want both, and putting a model behind a button that "
        "always does the same thing adds latency, cost and variance while buying nothing."
    )
