"""Shared Plotly theme for dvquys.com notebooks.

Clean, white, no gridlines, Figtree font, blog accent #0062a8.
Importing this module registers and activates the `dvq` template.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

ACCENT = "#0062a8"
ACCENT_SOFT = "#4C8BC4"
NEUTRAL = "#797979"
INK = "#1a1a1a"

FONT_FAMILY = "Figtree, system-ui, -apple-system, Helvetica, Arial, sans-serif"

# Categorical sequence: accent first, then complementary tones that work on white.
COLORWAY = [
    ACCENT,
    "#F58518",
    "#54A24B",
    "#B279A2",
    "#EECA3B",
    "#72B7B2",
    "#FF9DA6",
    "#9D755D",
]

_template = go.layout.Template(
    layout=go.Layout(
        font=dict(family=FONT_FAMILY, size=13, color=INK),
        title=dict(font=dict(family=FONT_FAMILY, size=16, color=INK), x=0, xanchor="left"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        colorway=COLORWAY,
        margin=dict(l=60, r=20, t=50, b=50),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor="#e5e5e5",
            ticks="outside",
            tickcolor="#cccccc",
            ticklen=4,
            title=dict(font=dict(size=12, color=NEUTRAL)),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor="#e5e5e5",
            ticks="outside",
            tickcolor="#cccccc",
            ticklen=4,
            title=dict(font=dict(size=12, color=NEUTRAL)),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            font=dict(size=12, color=INK),
        ),
        hoverlabel=dict(font=dict(family=FONT_FAMILY, size=12), bgcolor="white", bordercolor="#e5e5e5"),
    )
)

pio.templates["dvq"] = _template
pio.templates.default = "dvq"

# Use a renderer that emits HTML (with CDN-linked plotly.js) alongside the
# mimetype JSON, so Quarto-rendered notebooks display interactive figures.
pio.renderers.default = "plotly_mimetype+notebook_connected"
