"""The chart PNG export must never stall the report pipeline.

Kaleido rasterizes via a headless Chrome. On a machine without one it blocks
forever instead of raising, which previously hung every non-dry-run pipeline at
the HTML render step. These tests pin the degradation contract: bounded time,
empty string, no exception.
"""

from __future__ import annotations

import time

import pytest

from mexico_linkedin_jobs_portfolio.analytics import charts

pytestmark = pytest.mark.skipif(not charts.HAS_PLOTLY, reason="plotly is not installed")


def _figure():
    import plotly.graph_objects as go

    return go.Figure(data=[go.Bar(x=["a", "b"], y=[1, 2])])


def test_export_returns_empty_and_bounded_when_backend_stalls() -> None:
    """A wedged or absent Chrome degrades to no image inside the timeout."""
    started = time.monotonic()
    result = charts.figure_to_base64_png(_figure(), timeout_seconds=5)
    elapsed = time.monotonic() - started

    # Either a real PNG (Chrome present) or a clean empty string, never a hang.
    assert result == "" or result.startswith("data:image/png;base64,")
    assert elapsed < 60, f"export ran {elapsed:.1f}s; the timeout did not bound it"


def test_export_handles_missing_plotly_and_none_figure() -> None:
    assert charts.figure_to_base64_png(None) == ""


def test_timeout_is_configurable_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MX_JOBS_CHART_EXPORT_TIMEOUT", "12.5")
    import importlib

    reloaded = importlib.reload(charts)
    try:
        assert reloaded.CHART_EXPORT_TIMEOUT_SECONDS == 12.5
    finally:
        monkeypatch.delenv("MX_JOBS_CHART_EXPORT_TIMEOUT", raising=False)
        importlib.reload(charts)


if __name__ == "__main__":
    test_export_returns_empty_and_bounded_when_backend_stalls()
    test_export_handles_missing_plotly_and_none_figure()
    print("chart export timeout self-check passed")
