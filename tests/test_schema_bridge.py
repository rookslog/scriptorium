"""Tests for the lazy/optional scholar-schema bridge."""

from __future__ import annotations

from typing import Any

import pytest

from scriptorium.schema_bridge import (
    SchemaUnavailableError,
    schema_available,
    validate_page_gt,
)


def test_schema_available_returns_bool() -> None:
    assert isinstance(schema_available(), bool)


def test_validate_falls_back_when_schema_absent(minimal_page: dict[str, Any]) -> None:
    """Without scholar-schema installed, validation does a structural check and passes."""
    out = validate_page_gt(minimal_page, strict=False)
    assert out["page_index"] == 0


def test_strict_requires_schema_package(minimal_page: dict[str, Any]) -> None:
    """strict=True raises a clear error when no schema package is importable."""
    if schema_available():
        pytest.skip("scholar-schema is installed; strict path would succeed")
    with pytest.raises(SchemaUnavailableError, match="scholar-schema"):
        validate_page_gt(minimal_page, strict=True)


def test_structural_check_rejects_malformed() -> None:
    if schema_available():
        pytest.skip("scholar-schema installed; pydantic governs validation, not the fallback")
    with pytest.raises(ValueError, match="missing required keys"):
        validate_page_gt({"page_index": 0}, strict=False)
    with pytest.raises(ValueError, match="must be a list"):
        validate_page_gt({"page_index": 0, "regions": "nope"}, strict=False)
