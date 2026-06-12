"""Tests for the PageGT -> LaTeX -> PDF render path."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scriptorium.render import latex_escape, render_tex, tectonic_available


def test_render_tex_includes_body_and_footnote(minimal_page: dict[str, Any]) -> None:
    """The single-column template emits body text and a \\footnote for the note region."""
    tex = render_tex(minimal_page)
    assert r"\documentclass" in tex
    assert "Glaucon the son of Ariston" in tex
    assert r"\footnote{" in tex
    assert "Thracian goddess" in tex
    # The note region itself must not appear as a standalone body paragraph.
    assert tex.count("Thracian goddess") == 1


def test_render_tex_escapes_latex_specials() -> None:
    """LaTeX-special characters in body text are escaped, keeping the source compilable."""
    page = {
        "page_index": 0,
        "regions": [
            {
                "id": "b1",
                "label": "text_block",
                "bbox": {"x0": 0.1, "y0": 0.1, "x1": 0.9, "y1": 0.5},
                "text": "Cost was 50% of $100 & rising_fast #1",
            }
        ],
        "reading_order": ["b1"],
    }
    tex = render_tex(page)
    assert r"50\%" in tex
    assert r"\$100" in tex
    assert r"\&" in tex
    assert r"rising\_fast" in tex


def test_latex_escape_roundtrip() -> None:
    assert latex_escape("a_b") == r"a\_b"
    assert latex_escape("100%") == r"100\%"
    assert latex_escape("plain text") == "plain text"


def test_render_tex_title_block(minimal_page: dict[str, Any]) -> None:
    tex = render_tex(minimal_page)
    assert "The Republic, Book I" in tex
    assert "Plato" in tex


def test_render_pdf_emits_tex_without_engine(tmp_path: Path, minimal_page: dict[str, Any]) -> None:
    """render_pdf always writes the .tex source, even when tectonic is absent."""
    from scriptorium.render import render_pdf

    result = render_pdf(minimal_page, tmp_path)
    tex_path = tmp_path / "page.tex"
    assert tex_path.exists()
    assert result.tex == tex_path.read_text(encoding="utf-8")
    # gt is echoed back for downstream render-time additions.
    assert result.gt["page_index"] == 0


def test_tectonic_available_is_bool() -> None:
    assert isinstance(tectonic_available(), bool)
