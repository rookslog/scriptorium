"""Tests for the DegradationSpec input-language contract."""

from __future__ import annotations

import pytest

from scriptorium.degradation import DegradationSpec, apply


def test_clean_spec_is_noop() -> None:
    spec = DegradationSpec.clean()
    assert spec.is_noop()
    assert spec.severity == 0.0


def test_from_severity_scales_effects() -> None:
    spec = DegradationSpec.from_severity(0.5, seed=7)
    assert spec.severity == 0.5
    assert spec.skew == 0.5
    assert spec.noise == 0.5
    assert spec.jpeg_quality == 65  # 95 - 0.5*60
    assert spec.seed == 7
    assert not spec.is_noop()


def test_out_of_range_rejected() -> None:
    with pytest.raises(ValueError, match="severity"):
        DegradationSpec(severity=1.5)
    with pytest.raises(ValueError, match="jpeg_quality"):
        DegradationSpec(jpeg_quality=0)


def test_to_dict_roundtrips_fields() -> None:
    spec = DegradationSpec.from_severity(0.3)
    d = spec.to_dict()
    assert set(d) >= {"severity", "skew", "noise", "bleed_through", "shadow", "jpeg_quality"}


def test_apply_noop_returns_image_unchanged() -> None:
    sentinel = object()
    assert apply(sentinel, DegradationSpec.clean()) is sentinel


def test_apply_nonclean_not_yet_implemented() -> None:
    with pytest.raises(NotImplementedError, match="augraphy"):
        apply(object(), DegradationSpec.from_severity(0.5))
