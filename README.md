# nrt_agent_week2

Course site for **Week 2 of NRT Hot Topics: Agentic AI** — Introduction to AI Models.

Plain static HTML. No build step, no Jekyll, no dependencies. Open `index.html` in a browser to
preview locally, or push and enable GitHub Pages.

```
index.html                     the single main page
assets/css/style.css           the whole stylesheet
assets/img/                    MSU and CMSE marks
guides/demo1.html              rendered guide for demo 1
downloads/demo1_*.zip          the demo package students download
.nojekyll                      tells GitHub Pages to serve the files as-is
```

## Publishing

```bash
git add -A && git commit -m "Week 2 site" && git push
```

Then **Settings → Pages → Source: deploy from branch → main / (root)**.
The site appears at `https://<user>.github.io/nrt_agent_week2/`.

## Adding demos 2–4

Each demo needs two things:

1. `downloads/demoN_<name>.zip`
2. `guides/demoN.html` — built from a markdown guide with the same template as demo 1

Then in `index.html`, find the matching `<div class="level pending">`, remove `pending` from the
class, and replace the two disabled `<span class="btn">` elements with real links:

```html
<a class="btn" href="downloads/demo2_mcp_tissue_analyzer.zip">Download demo 2 &nbsp;↓</a>
<a class="btn btn-ghost" href="guides/demo2.html">Open the guide</a>
```

The `<span class="tag">In preparation</span>` can be deleted at the same time.

## Regenerating a guide page from markdown

The guides are plain HTML, so they can be hand-edited. If you prefer to keep writing markdown:

```bash
pip install markdown
python3 - <<'PY'
import markdown
from pathlib import Path
body = markdown.markdown(Path("DemoN_guide.md").read_text(),
                         extensions=["tables", "fenced_code", "attr_list"])
tpl = Path("guides/demo1.html").read_text()
# swap the content between the backlink and the closing note
PY
```

Simpler in practice: copy `guides/demo1.html`, keep the header and footer, and replace the middle.
