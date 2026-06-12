"""scriptorium -- schema-first synthetic scholarly corpus generator.

scriptorium manufactures ground truth instead of annotating it: it typesets trusted
public-domain texts into scholarly PDF layouts and degrades them into scan-like images,
emitting (PDF/image, perfect ground-truth) pairs.

Design rule: **schema-first generation**. The input language IS a DocumentGT/PageGT
instance plus a degradation spec, so GT alignment holds by construction and every schema
element must earn a renderer.

The walking skeleton (milestone 1) renders a single-column page with one footnote from a
minimal PageGT-shaped JSON fixture. See ``docs/design.md`` for the full input-language
contract and the template roadmap.
"""

from __future__ import annotations

from scriptorium.degradation import DegradationSpec
from scriptorium.render import RenderResult, render_pdf, render_tex

__all__ = [
    "DegradationSpec",
    "RenderResult",
    "render_pdf",
    "render_tex",
]

__version__ = "0.0.1"
