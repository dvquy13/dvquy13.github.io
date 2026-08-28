---
paths:
  - "**/*.ipynb"
---

# Jupyter Notebook Posts — Rules

For `.ipynb` files published as blog posts (e.g. `projects/<slug>/index.ipynb`).

## Render List Inclusion

`_quarto.yml` `project.render:` must include `**/*.ipynb` — otherwise notebooks are silently skipped and never appear on the site. Adding a notebook to `posts/` or `projects/` is not enough on its own.

## Frontmatter via Raw Cell

The first cell must be a **raw** cell containing YAML frontmatter between `---` markers:

```
---
title: "Post Title"
subtitle: "..."
date: "YYYY-MM-DD"
categories: [tech, ml]
keywords: "comma, separated"
draft: true
---
```

**Strip the duplicate H1** from the first markdown cell — the frontmatter `title:` becomes the banner heading, and leaving a `# ...` H1 in the body produces two stacked titles.

**Name the file `index.ipynb`** (not `notebook.ipynb`) so the URL becomes `/<folder>/<slug>/` rather than `/<folder>/<slug>/notebook.html`.

## Plotly + Quarto

Quarto silently drops Plotly's default `application/vnd.plotly.v1+json` MIME output (renders as "Unable to display output for mime type(s)"). Setting `pio.renderers.default = "plotly_mimetype+notebook_connected"` is **not enough** — the connected renderer emits the loader script and the figure data as separate outputs, and Quarto doesn't merge them.

**Use this pattern for every figure:**

```python
from IPython.display import HTML
HTML(fig.to_html(
    include_plotlyjs="cdn",
    full_html=False,
    div_id="fig-unique-id",
    config={"responsive": True},
    default_width="100%",
    default_height="380px",
))
```

This produces one self-contained `text/html` output with the plotly.js CDN link, the figure div, and the render call inline. Quarto embeds it directly.

**Do not set `width=N` in `fig.update_layout(...)`** — use `autosize=True` instead so the figure fills its container. The hardcoded width fights the responsive config.

## Figure Width vs. TOC

With the right-side TOC visible, the body column shrinks to ~555px. To extend a figure past that, add a Quarto cell directive at the top of the code cell:

```python
#| column: page
```

`column: page` extends to the full body-width (~885px). Other options:
- `column-body-outset` — slightly wider than body
- `column-screen-inset` — full viewport with small margins
- `column-screen` — edge-to-edge

The directive wraps the cell output in `<div class="column-page">`; Quarto auto-collapses the TOC into a dropdown to make room.

## DataFrame Tables

Prefer rendered HTML tables over plain text. Return the DataFrame as the last expression in a cell — Quarto captures the `text/html` output and renders it as a proper table:

```python
df.round(4).set_index("model")  # renders as HTML table
```

Avoid `print(df.to_string(...))` — it forces monospace text output and loses table formatting.

For DataFrames inside loops (e.g. multiple confusion matrices), use `display()`:

```python
from IPython.display import display
display(pd.DataFrame(cm, index=[...], columns=[...]))
```

## Editing Markdown Cells with NotebookEdit

**`NotebookEdit` writes `source` as a single string, breaking paragraph rendering.** nbformat expects `source` to be a list of lines; when it's a plain string, Quarto collapses all `\n\n` paragraph breaks so multi-paragraph markdown cells render as one unbroken blob.

After any `NotebookEdit` session that touched multi-paragraph markdown cells, normalize with:

```bash
python3 -c "
import json
p = 'projects/<slug>/index.ipynb'
nb = json.load(open(p))
for c in nb['cells']:
    if isinstance(c.get('source'), str):
        c['source'] = c['source'].splitlines(keepends=True)
json.dump(nb, open(p, 'w'), indent=1, ensure_ascii=False)
open(p, 'a').write('\n')
"
```

Verify by checking paragraph counts in-browser — not just that the heading renders.

**Never put a `## heading`, `$$` display math, and body prose in the same markdown cell.** Quarto's notebook renderer swallows the entire cell into the `<h2>` element, making the section disappear as body content. Keep the `## heading` in its own cell; put body prose and math in the cell(s) that follow.

## Papermill Workflow

Re-execute notebooks in place with papermill so the cell outputs are stored in the `.ipynb` itself:

```bash
uv run papermill index.ipynb index.ipynb --no-progress-bar
```

Combined with `freeze: true` in `posts/_metadata.yml` / `projects/_metadata.yml`, the embedded outputs are what Quarto renders — no Python kernel registration or re-execution at build time. Just commit the executed notebook.

When iterating on a cell, clear outputs + execution_count for all code cells before re-running so the diff stays clean.

## Avoiding Session Bloat During Iteration

`Read` and `NotebookEdit` both dump the full notebook JSON (including every embedded base64 image output) into the transcript — `Read` on every call, `NotebookEdit` via its `toolUseResult`. On a plot-heavy notebook, an "iterate until target metric" loop that repeatedly Read/edits an output-populated `.ipynb` can balloon the session to tens of MB in a few dozen turns, which risks 529 errors on resume later.

- **Compute outside the notebook.** Run experiment/tuning loops as a plain script via `Bash` (`uv run ...`), writing small CSV/parquet results to disk. Evaluate progress by reading those result files, not the notebook.
- **Clear outputs before a round of edits.** Strip cell outputs (see snippet above) before a batch of `Read`/`NotebookEdit` calls; only run the final `papermill` re-execute once, after all edits are done.
- **Evaluate narrowly.** To check notebook content mid-loop, parse just the relevant cell via a `python3 -c` snippet through `Bash` instead of a full `Read`.
