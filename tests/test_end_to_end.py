"""End-to-end render test: fixture -> .tex -> tectonic -> a one-page PDF.

Marked ``tectonic`` and auto-skipped when the engine is not installed (e.g. in CI until
tectonic is provisioned). The skip reason is explicit per the project requirement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scriptorium.render import render_pdf, tectonic_available

pytestmark = pytest.mark.tectonic

_skip_no_tectonic = pytest.mark.skipif(
    not tectonic_available(),
    reason="tectonic not installed",
)


def _pdf_page_count(pdf_path: Path) -> int:
    """Count pages in a PDF robustly (handles FlateDecode-compressed object streams)."""
    from pypdf import PdfReader

    return len(PdfReader(str(pdf_path)).pages)


@_skip_no_tectonic
def test_render_pdf_produces_one_page(tmp_path: Path, minimal_page: dict[str, Any]) -> None:
    result = render_pdf(minimal_page, tmp_path)
    assert result.pdf_path is not None
    assert result.pdf_path.exists()
    pdf_bytes = result.pdf_path.read_bytes()
    assert pdf_bytes.startswith(b"%PDF")
    assert _pdf_page_count(result.pdf_path) == 1
