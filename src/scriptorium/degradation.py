"""Degradation specification: the second half of the input language.

A :class:`DegradationSpec` is a severity-parameterized description of how a clean rendered
page is degraded toward a scan-like image. The plan (PLAN.md Sec 5, GT-A) names augraphy as
the eventual scan-simulation backend; it is **planned, not yet integrated**. Until then the
spec is the stable contract and only a small Pillow-based reference implementation of a few
effects exists (see :func:`apply` -- intentionally a no-op stub for the walking skeleton).

The spec exists at milestone 1 so that callers can already author the full
(PageGT + DegradationSpec) input language; the renderers grow to honor each field.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any


@dataclass(frozen=True, slots=True)
class DegradationSpec:
    """Severity-parameterized scan-degradation spec.

    Every effect is scaled by ``severity`` in [0.0, 1.0]; per-effect magnitudes scale the
    effect within that envelope. ``severity == 0.0`` means "leave the clean render
    untouched" (the walking-skeleton default).

    Fields map to the PLAN.md Sec 5 augraphy effect families:
        skew:          page rotation (degrees at severity 1.0).
        noise:         additive sensor/paper noise magnitude.
        bleed_through: ghost of the verso showing through the page.
        shadow:        scanner/binding shadow gradient.
        jpeg_quality:  output JPEG quality (lower == more block artifacts).

    TODO(augraphy): replace the Pillow reference effects with an augraphy pipeline
    constructed from these fields so degradation matches real scanner physics.
    """

    severity: float = 0.0
    skew: float = 0.0
    noise: float = 0.0
    bleed_through: float = 0.0
    shadow: float = 0.0
    jpeg_quality: int = 95
    seed: int | None = None

    def __post_init__(self) -> None:
        for name in ("severity", "skew", "noise", "bleed_through", "shadow"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                msg = f"{name} must be in [0.0, 1.0], got {value}"
                raise ValueError(msg)
        if not 1 <= self.jpeg_quality <= 100:
            msg = f"jpeg_quality must be in [1, 100], got {self.jpeg_quality}"
            raise ValueError(msg)

    @classmethod
    def clean(cls) -> DegradationSpec:
        """A no-op spec: the clean render passes through unchanged."""
        return cls()

    @classmethod
    def from_severity(cls, severity: float, *, seed: int | None = None) -> DegradationSpec:
        """Build a spec where every effect is driven by a single severity dial.

        A convenience for sweeps where difficulty is a single controlled variable
        (PLAN.md Sec 5: "difficulty as a controlled variable"). Per-effect magnitudes are
        set to ``severity`` and JPEG quality is interpolated from 95 (clean) down to 35.
        """
        if not 0.0 <= severity <= 1.0:
            msg = f"severity must be in [0.0, 1.0], got {severity}"
            raise ValueError(msg)
        jpeg_quality = round(95 - severity * 60)
        return cls(
            severity=severity,
            skew=severity,
            noise=severity,
            bleed_through=severity,
            shadow=severity,
            jpeg_quality=jpeg_quality,
            seed=seed,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize for echoing into the emitted GT manifest."""
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def is_noop(self) -> bool:
        """True if applying this spec leaves the image unchanged."""
        return self.severity == 0.0


def apply(image: Any, spec: DegradationSpec) -> Any:
    """Apply a degradation spec to a Pillow image (reference stub).

    The walking skeleton ships a deliberate near-no-op: a clean spec returns the image
    untouched, and any non-clean spec currently raises NotImplementedError rather than
    pretending to simulate a scanner. This keeps the contract honest until the augraphy
    backend lands.

    Args:
        image: a ``PIL.Image.Image``.
        spec: the degradation specification.

    Returns:
        The (possibly degraded) image.

    Raises:
        NotImplementedError: if a non-clean spec is supplied (augraphy not yet integrated).
    """
    if spec.is_noop():
        return image
    msg = (
        "Non-clean DegradationSpec requested but the scan-simulation backend (augraphy) "
        "is not yet integrated. See docs/design.md (degradation roadmap)."
    )
    raise NotImplementedError(msg)


# Suppress unused-import style lint noise for the dataclass `field` helper, which is kept
# imported for the roadmap effects that will need default_factory lists.
_ = field
