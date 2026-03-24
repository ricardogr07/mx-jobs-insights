"""Local-first Streamlit dashboard for Phase 3."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from mexico_linkedin_jobs_portfolio.models import DashboardState, LatestJobRecord, SiteReportEntry
from mexico_linkedin_jobs_portfolio.presentation import DashboardDataLoader

DEFAULT_REPORT_ROOT = Path("artifacts/reports")
DEFAULT_CURATED_ROOT = Path("artifacts/curated")


def main() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="Mexico LinkedIn Jobs Portfolio",
        page_icon="M",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css(st)

    st.title("Mexico LinkedIn Jobs Portfolio")
    st.caption(
        "Local-first dashboard over curated DuckDB/Parquet data and reviewed Phase 2 report artifacts."
    )

    loader = DashboardDataLoader()
    report_root = _sidebar_path_input(
        st,
        label="Report root",
        default_value=DEFAULT_REPORT_ROOT,
        help_text="Directory containing completed Phase 2 report bundles.",
    )
    curated_root = _sidebar_path_input(
        st,
        label="Curated root",
        default_value=DEFAULT_CURATED_ROOT,
        help_text="Directory containing curated DuckDB and Parquet outputs.",
    )

    try:
        baseline_state = loader.load(report_root=report_root, curated_root=curated_root)
    except Exception as exc:
        st.error(f"Unable to load dashboard data: {exc}")
        st.stop()

    selected_cadence, selected_period_id = _render_sidebar_selection(
        st,
        baseline_state,
        report_root=report_root,
        curated_root=curated_root,
    )
    try:
        dashboard_state = loader.load(
            report_root=report_root,
            curated_root=curated_root,
            cadence=selected_cadence,
            period_id=selected_period_id,
        )
    except Exception as exc:
        st.error(f"Unable to load the selected report period: {exc}")
        st.stop()

    _render_summary_row(st, dashboard_state)

    overview_tab, report_tab, private_tab = st.tabs(
        ["Overview", "Public report", "Local-only private drill-down"]
    )
    with overview_tab:
        _render_overview(st, dashboard_state)
    with report_tab:
        _render_public_report(st, dashboard_state)
    with private_tab:
        _render_private_drilldown(st, dashboard_state)


def _sidebar_path_input(st, *, label: str, default_value: Path, help_text: str) -> Path:
    value = st.sidebar.text_input(label, value=str(default_value), help=help_text)
    return Path(value).expanduser()


def _render_sidebar_selection(
    st,
    baseline_state: DashboardState,
    *,
    report_root: Path,
    curated_root: Path,
) -> tuple[str | None, str | None]:
    st.sidebar.header("Report selection")

    cadence_choice = st.sidebar.selectbox(
        "Cadence",
        options=("latest", "weekly", "monthly"),
        index=0,
        help="Choose the latest available report or lock to a cadence.",
    )

    period_id: str | None = None
    cadence: str | None = None
    if cadence_choice == "weekly":
        cadence = "weekly"
        entries = list(baseline_state.report_index.weekly_entries)
        if entries:
            period_id = st.sidebar.selectbox(
                "Weekly period",
                options=[entry.period_id for entry in entries],
                index=0,
            )
        else:
            st.sidebar.info("No weekly report bundles are available yet.")
    elif cadence_choice == "monthly":
        cadence = "monthly"
        entries = list(baseline_state.report_index.monthly_entries)
        if entries:
            period_id = st.sidebar.selectbox(
                "Monthly period",
                options=[entry.period_id for entry in entries],
                index=0,
            )
        else:
            st.sidebar.info("No monthly report bundles are available yet.")
    else:
        st.sidebar.caption("Using the latest available report bundle.")

    st.sidebar.divider()
    st.sidebar.header("Data roots")
    st.sidebar.code(str(report_root), language="text")
    st.sidebar.code(str(curated_root), language="text")
    return cadence, period_id


def _render_summary_row(st, state: DashboardState) -> None:
    columns = st.columns(4)
    columns[0].metric("Reports", state.report_index.report_count)
    columns[1].metric(
        "Latest weekly", _summary_period(state.report_index.latest_weekly, state.report_index.latest_weekly)
    )
    columns[2].metric(
        "Latest monthly",
        _summary_period(state.report_index.latest_monthly, state.report_index.latest_monthly),
    )
    columns[3].metric("Selected jobs", len(state.selected_latest_jobs))


def _render_overview(st, state: DashboardState) -> None:
    st.subheader("Public-safe overview")
    selected_entry = state.selected_entry
    if selected_entry is None:
        st.info("No report bundle matched the current selection.")
        return

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown(
            f"**Selected period:** `{selected_entry.cadence}` `{selected_entry.period_id}`  \n"
            f"**Range:** `{selected_entry.period_start.isoformat()}` to `{selected_entry.period_end.isoformat()}`  \n"
            f"**Locale coverage:** {', '.join(selected_entry.locale_coverage)}"
        )
        st.markdown("**Report assets**")
        st.write(_artifact_links(selected_entry))

    with right:
        st.markdown("**Top metrics**")
        st.metric("Jobs", selected_entry.metrics.job_count)
        st.metric("Observations", selected_entry.metrics.observation_count)
        st.metric("Source runs", selected_entry.metrics.source_run_count)

    st.markdown("**Top cities**")
    st.table(_counts_table(selected_entry.metrics.city_counts[:5]))
    st.markdown("**Top tech stack terms**")
    st.table(_counts_table(selected_entry.metrics.tech_stack_counts[:5]))

    st.markdown("**Available report bundles**")
    st.table(_reports_table(state.report_index.entries[:8]))


def _render_public_report(st, state: DashboardState) -> None:
    st.subheader("Public report artifacts")
    selected_entry = state.selected_entry
    if selected_entry is None:
        st.info("No selected report bundle to preview.")
        return

    markdown_paths = selected_entry.summary.markdown_paths or {}
    html_paths = selected_entry.summary.html_paths or {}
    markdown_path = markdown_paths.get("en") or markdown_paths.get("es")
    html_path = html_paths.get("en") or html_paths.get("es")

    left, right = st.columns(2)
    with left:
        st.markdown("**Markdown preview**")
        if markdown_path is not None:
            st.code(markdown_path.read_text(encoding="utf-8"), language="markdown")
        else:
            st.info("No Markdown file is available for this bundle.")
    with right:
        st.markdown("**HTML snapshot path**")
        if html_path is not None:
            st.code(str(html_path), language="text")
        else:
            st.info("No HTML file is available for this bundle.")


def _render_private_drilldown(st, state: DashboardState) -> None:
    st.subheader("Local-only private drill-down")
    st.caption("This section is for local validation only and includes non-public fields.")

    if not state.selected_latest_jobs:
        st.info("No job-level rows are available for the selected report period.")
        return

    selected_job_id = st.selectbox(
        "Job",
        options=[job.job_id for job in state.selected_latest_jobs],
        format_func=lambda job_id: _job_label(state.selected_latest_jobs, job_id),
    )
    job = next(job for job in state.selected_latest_jobs if job.job_id == selected_job_id)

    st.markdown(
        f"**Company:** {job.company_name or 'Unknown'}  \n"
        f"**URL:** {job.job_url or 'Unknown'}  \n"
        f"**Description:**"
    )
    st.write(job.description_text or "Unknown")
    st.markdown("**Structured row**")
    st.table([_job_details_row(job)])


def _job_details_row(job: LatestJobRecord) -> dict[str, str]:
    payload = asdict(job)
    payload["observed_at"] = job.observed_at.isoformat()
    payload["tech_stack"] = " | ".join(job.tech_stack)
    return {key: "" if value is None else str(value) for key, value in payload.items()}


def _job_label(jobs: tuple[LatestJobRecord, ...], job_id: str) -> str:
    job = next(item for item in jobs if item.job_id == job_id)
    company = job.company_name or "Unknown company"
    return f"{job.title} | {company} | {job.city}"


def _counts_table(counts) -> list[dict[str, str | int]]:
    return [{"label": item.label, "count": item.count} for item in counts]


def _reports_table(entries: tuple[SiteReportEntry, ...]) -> list[dict[str, str | int]]:
    return [
        {
            "period_id": entry.period_id,
            "cadence": entry.cadence,
            "jobs": entry.metrics.job_count,
            "observations": entry.metrics.observation_count,
            "locale_coverage": ", ".join(entry.locale_coverage),
        }
        for entry in entries
    ]


def _artifact_links(entry: SiteReportEntry) -> list[str]:
    links: list[str] = []
    if entry.summary.metrics_path is not None:
        links.append(f"metrics: {entry.summary.metrics_path}")
    if entry.summary.public_csv_path is not None:
        links.append(f"public csv: {entry.summary.public_csv_path}")
    for locale, path in (entry.summary.markdown_paths or {}).items():
        links.append(f"markdown[{locale}]: {path}")
    for locale, path in (entry.summary.html_paths or {}).items():
        links.append(f"html[{locale}]: {path}")
    return links


def _summary_period(entry: SiteReportEntry | None, fallback: SiteReportEntry | None) -> str:
    resolved = entry or fallback
    return resolved.period_id if resolved is not None else "-"


def _inject_css(st) -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(193, 132, 58, 0.12), transparent 28%),
                radial-gradient(circle at top right, rgba(19, 78, 74, 0.12), transparent 24%),
                linear-gradient(180deg, #faf7f0 0%, #f3efe6 100%);
            color: #1f2933;
        }
        h1, h2, h3 {
            font-family: Georgia, "Times New Roman", serif;
            letter-spacing: 0.01em;
        }
        .stMetric {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(31, 41, 51, 0.08);
            border-radius: 14px;
            padding: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()



