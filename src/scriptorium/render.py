"""Rendering: PageGT JSON -> LaTeX -> PDF.

The walking skeleton (milestone 1) renders a single-column page with one footnote. The
input is a PageGT-shaped mapping; the output is a ``.tex`` source and, when the tectonic
engine is available, a one-page PDF.

Schema-first design rule: the renderer consumes regions/elements from the PageGT and
*every schema element must earn a renderer*. Milestone 1 covers ``text_block`` regions and
``note`` (footnote) semantics; later milestones add marginal reference numbers, sous
rature, dual-register columns, and commentary frames (see docs/design.md).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jinja2

from scriptorium.schema_bridge import validate_page_gt

_TEMPLATE_DIR = Path(__file__).parent / "templates"

# A LaTeX-safe Jinja2 environment. LaTeX uses { } % # everywhere, so we use delimiters that
# do not collide with TeX syntax.
_JINJA_ENV = jinja2.Environment(
    block_start_string=r"\BLOCK{",
    block_end_string="}",
    variable_start_string=r"\VAR{",
    variable_end_string="}",
    comment_start_string=r"\#{",
    comment_end_string="}",
    line_statement_prefix="%%",
    line_comment_prefix="%#",
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
)

# Minimal LaTeX escaping for body text drawn from public-domain sources.
_LATEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def latex_escape(text: str) -> str:
    """Escape LaTeX-special characters in plain body text."""
    out: list[str] = []
    for ch in text:
        out.append(_LATEX_ESCAPES.get(ch, ch))
    return "".join(out)


_JINJA_ENV.filters["latex"] = latex_escape


@dataclass(frozen=True, slots=True)
class RenderResult:
    """Result of rendering a PageGT.

    Attributes:
        tex: the generated LaTeX source.
        pdf_path: path to the rendered PDF, or None if no engine was available.
        gt: the input PageGT echoed back (the basis for render-time GT additions such as
            bboxes; milestone 1 echoes the validated input unchanged).
    """

    tex: str
    pdf_path: Path | None
    gt: dict[str, Any]


def tectonic_available() -> bool:
    """True if the tectonic engine is on PATH."""
    return shutil.which("tectonic") is not None


class _FootnoteCollector:
    """Splits a PageGT's regions into body text and footnotes for the single-column template.

    Milestone 1 contract:
    - A region whose ``label == "note_area"`` OR whose ``semantic_labels`` contains "note"
      is a footnote. Its body marker (the in-text ``\\footnotemark`` anchor) is identified by
      a region carrying a ``footnote_marker`` ref in its ``extra`` data, or -- in the simplest
      fixture -- the footnote is attached at the end of the single text block.
    - All other regions with text are body text, emitted in ``reading_order`` if present.
    """

    def __init__(self, page_gt: dict[str, Any]) -> None:
        self._regions: dict[str, dict[str, Any]] = {
            r["id"]: r for r in page_gt.get("regions", []) if "id" in r
        }
        self._order: list[str] = page_gt.get("reading_order") or list(self._regions)

    @staticmethod
    def _is_note(region: dict[str, Any]) -> bool:
        return region.get("label") == "note_area" or "note" in region.get("semantic_labels", [])

    def body_regions(self) -> list[dict[str, Any]]:
        return [
            self._regions[rid]
            for rid in self._order
            if rid in self._regions and not self._is_note(self._regions[rid])
        ]

    def note_regions(self) -> list[dict[str, Any]]:
        return [
            self._regions[rid]
            for rid in self._order
            if rid in self._regions and self._is_note(self._regions[rid])
        ]


def render_tex(page_gt: dict[str, Any], *, strict_schema: bool = False) -> str:
    """Render a PageGT-shaped dict to LaTeX source (no engine required).

    Args:
        page_gt: a PageGT-shaped mapping (the input language).
        strict_schema: require the scholar-schema package for validation (see schema_bridge).

    Returns:
        LaTeX source as a string.
    """
    validated = validate_page_gt(page_gt, strict=strict_schema)
    collector = _FootnoteCollector(validated)

    body_regions = collector.body_regions()
    note_regions = collector.note_regions()

    # Milestone-1 footnote attachment: the first footnote attaches to the first body block.
    # The marker is inserted at the body block's `footnote_anchor` char offset if given,
    # else appended. This keeps the marker<->note pairing exact for GT.
    notes = [
        {"id": n["id"], "text": (n.get("text") or "").strip()}
        for n in note_regions
        if (n.get("text") or "").strip()
    ]

    template = _JINJA_ENV.get_template("single_column.tex.j2")
    source = validated.get("source", {})
    return template.render(
        page_label=validated.get("page_label"),
        title=source.get("title"),
        author=source.get("author"),
        body_regions=body_regions,
        notes=notes,
    )


def render_pdf(
    page_gt: dict[str, Any],
    out_dir: Path | str,
    *,
    strict_schema: bool = False,
    stem: str = "page",
) -> RenderResult:
    """Render a PageGT to a PDF via tectonic.

    Args:
        page_gt: a PageGT-shaped mapping.
        out_dir: directory to write ``<stem>.tex`` and ``<stem>.pdf`` into.
        strict_schema: require scholar-schema for validation.
        stem: filename stem for the emitted artifacts.

    Returns:
        RenderResult with the tex source, the PDF path (None if tectonic is absent), and
        the echoed GT.

    Raises:
        RuntimeError: if tectonic is present but the compilation fails.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    validated = validate_page_gt(page_gt, strict=strict_schema)
    tex = render_tex(validated, strict_schema=strict_schema)
    tex_path = out_dir / f"{stem}.tex"
    tex_path.write_text(tex, encoding="utf-8")

    if not tectonic_available():
        return RenderResult(tex=tex, pdf_path=None, gt=validated)

    pdf_path = _compile_with_tectonic(tex_path, out_dir, stem)
    return RenderResult(tex=tex, pdf_path=pdf_path, gt=validated)


def _compile_with_tectonic(tex_path: Path, out_dir: Path, stem: str) -> Path:
    """Compile a .tex file to PDF using tectonic, returning the PDF path."""
    with tempfile.TemporaryDirectory(prefix="scriptorium-tectonic-") as cache:
        proc = subprocess.run(
            [
                "tectonic",
                "--chatter",
                "minimal",
                "--outdir",
                str(out_dir),
                str(tex_path),
            ],
            capture_output=True,
            text=True,
            env={"TECTONIC_CACHE_DIR": cache, "PATH": _path_env()},
            check=False,
        )
    pdf_path = out_dir / f"{stem}.pdf"
    if proc.returncode != 0 or not pdf_path.exists():
        msg = (
            f"tectonic failed (exit {proc.returncode}).\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
        raise RuntimeError(msg)
    return pdf_path


def _path_env() -> str:
    """Return a PATH that includes tectonic's directory."""
    import os

    return os.environ.get("PATH", "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin")
