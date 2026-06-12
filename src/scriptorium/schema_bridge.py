"""Lazy bridge to the scholar-schema package.

scriptorium's input language is a ``DocumentGT``/``PageGT`` instance (the schema-first
design rule). The canonical models live in the ``scholar-schema`` package, which is being
built **in parallel** at github.com/loganrooks/scholar-schema and may not exist yet.

To keep scriptorium usable before that repo is published, every import of the schema
package is funneled through this module and is **lazy and optional**:

- ``load_schema()`` attempts the import on demand and raises a clear, actionable error if
  the package is absent.
- ``validate_page_gt()`` validates a raw dict against the real pydantic model *if* the
  package is installed, and otherwise falls back to a minimal structural check so the
  walking skeleton runs on hand-written JSON with no schema dependency.

TODO(scholar-schema): once the repo is published and pinned (see pyproject ``[schema]``
extra), make validation strict by default and drop the structural fallback.
"""

from __future__ import annotations

from types import ModuleType
from typing import Any

# The published package distribution name is "scholar-schema"; its import package is
# expected to be "scholar_schema". scholardoc's reference clone exposes the same models
# under the legacy "scholargt" namespace, so we probe both for forward/backward compat.
_CANDIDATE_MODULES = ("scholar_schema.schema", "scholargt.schema")


class SchemaUnavailableError(ImportError):
    """Raised when the scholar-schema package is required but not installed."""


def load_schema() -> ModuleType:
    """Import and return the schema module, trying each candidate namespace.

    Raises:
        SchemaUnavailableError: if no candidate module can be imported. The message
            explains how to install the (parallel, not-yet-published) package.
    """
    import importlib

    last_err: Exception | None = None
    for name in _CANDIDATE_MODULES:
        try:
            return importlib.import_module(name)
        except ImportError as err:
            last_err = err
    msg = (
        "scholar-schema is not installed. It is built in parallel at "
        "github.com/loganrooks/scholar-schema and is an OPTIONAL dependency of "
        "scriptorium. Install it with `uv sync --extra schema` once the repo exists. "
        "Until then, scriptorium operates on raw PageGT-shaped JSON without strict "
        "validation."
    )
    raise SchemaUnavailableError(msg) from last_err


def schema_available() -> bool:
    """Return True if a schema package can be imported, without raising."""
    try:
        load_schema()
    except SchemaUnavailableError:
        return False
    return True


_REQUIRED_PAGE_KEYS = ("page_index", "regions")


def validate_page_gt(data: dict[str, Any], *, strict: bool = False) -> dict[str, Any]:
    """Validate a raw PageGT-shaped dict.

    If scholar-schema is installed, validate against the real ``PageGT`` model and return
    the round-tripped dict. Otherwise fall back to a minimal structural check unless
    ``strict`` is requested.

    Args:
        data: a PageGT-shaped mapping (the input language).
        strict: if True, require the schema package and raise if it is missing.

    Returns:
        The validated dict (round-tripped through the model when available).

    Raises:
        SchemaUnavailableError: if ``strict`` and the schema package is missing.
        ValueError: if the structural fallback finds the dict malformed.
    """
    try:
        schema = load_schema()
    except SchemaUnavailableError:
        if strict:
            raise
        return _structural_check(data)

    page_gt_cls = schema.PageGT
    model = page_gt_cls.model_validate(data)
    dumped: dict[str, Any] = model.model_dump(mode="json", exclude_none=True)
    return dumped


def _structural_check(data: dict[str, Any]) -> dict[str, Any]:
    """Minimal PageGT shape check used when scholar-schema is unavailable."""
    missing = [k for k in _REQUIRED_PAGE_KEYS if k not in data]
    if missing:
        msg = f"PageGT-shaped JSON missing required keys: {missing}"
        raise ValueError(msg)
    if not isinstance(data["regions"], list):
        msg = "PageGT 'regions' must be a list"
        raise ValueError(msg)
    return data
