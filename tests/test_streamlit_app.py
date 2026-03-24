from __future__ import annotations

import sys
from pathlib import Path

from mexico_linkedin_jobs_portfolio.interfaces.streamlit import app as streamlit_app
from mexico_linkedin_jobs_portfolio.presentation import DashboardDataLoader
from tests.presentation_fixtures import write_report_fixtures


class _ContextBlock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def metric(self, *args, **kwargs):
        return None

    def markdown(self, *args, **kwargs):
        return None

    def write(self, *args, **kwargs):
        return None

    def table(self, *args, **kwargs):
        return None

    def info(self, *args, **kwargs):
        return None

    def code(self, *args, **kwargs):
        return None


class _Sidebar(_ContextBlock):
    def text_input(self, label, value=None, help=None):
        return value

    def header(self, *args, **kwargs):
        return None

    def selectbox(self, label, options, index=0, format_func=None, help=None):
        return options[index] if options else None

    def caption(self, *args, **kwargs):
        return None

    def divider(self):
        return None


class _StreamlitStub(_ContextBlock):
    def __init__(self) -> None:
        self.sidebar = _Sidebar()

    def set_page_config(self, *args, **kwargs):
        return None

    def title(self, *args, **kwargs):
        return None

    def caption(self, *args, **kwargs):
        return None

    def error(self, message):
        raise AssertionError(f"Unexpected Streamlit error: {message}")

    def stop(self):
        raise AssertionError("Streamlit stop should not be triggered in the smoke test")

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return [_ContextBlock() for _ in range(count)]

    def tabs(self, labels):
        return [_ContextBlock() for _ in labels]

    def subheader(self, *args, **kwargs):
        return None

    def selectbox(self, label, options, index=0, format_func=None, help=None):
        return options[index] if options else None


def test_dashboard_data_loader_keeps_private_fields_for_selected_period(tmp_path: Path) -> None:
    curated_root, report_root = write_report_fixtures(tmp_path)

    state = DashboardDataLoader().load(report_root=report_root, curated_root=curated_root)

    assert state.selected_entry is not None
    assert state.selected_entry.period_id == "2026-03"
    assert len(state.selected_latest_jobs) == 2
    first_job = state.selected_latest_jobs[0]
    assert first_job.company_name is not None
    assert first_job.job_url is not None
    assert first_job.description_text is not None


def test_streamlit_app_main_runs_with_stub_streamlit(tmp_path: Path, monkeypatch) -> None:
    curated_root, report_root = write_report_fixtures(tmp_path)
    stub = _StreamlitStub()

    monkeypatch.setitem(sys.modules, "streamlit", stub)
    monkeypatch.setattr(streamlit_app, "DEFAULT_REPORT_ROOT", report_root)
    monkeypatch.setattr(streamlit_app, "DEFAULT_CURATED_ROOT", curated_root)

    streamlit_app.main()
