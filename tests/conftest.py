"""Shared pytest fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

_FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def minimal_page() -> dict[str, Any]:
    """The hand-written minimal PageGT-shaped fixture (single column + one footnote)."""
    raw = (_FIXTURE_DIR / "minimal_page.json").read_text(encoding="utf-8")
    return json.loads(raw)  # type: ignore[no-any-return]
