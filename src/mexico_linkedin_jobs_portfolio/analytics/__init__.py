"""Analytics helpers for report generation."""

from mexico_linkedin_jobs_portfolio.analytics.dataset import (
    CuratedDataset,
    CuratedDatasetReader,
    JoinedObservationRecord,
)
from mexico_linkedin_jobs_portfolio.analytics.metrics import (
    MetricsBuildResult,
    build_report_metrics,
)
from mexico_linkedin_jobs_portfolio.analytics.periods import (
    resolve_closed_period,
    resolve_reference_date,
)

try:
    from mexico_linkedin_jobs_portfolio.analytics.charts import (
        create_all_charts,
        create_employment_type_chart,
        create_industry_distribution_chart,
        create_jobs_distribution_map,
        create_remote_distribution_chart,
        create_seniority_distribution_chart,
        create_tech_stack_overview_heatmap,
        create_top_cities_chart,
        create_top_companies_chart,
        create_top_tech_stack_chart,
        create_word_cloud_text,
        figure_to_base64_png,
    )
    from mexico_linkedin_jobs_portfolio.analytics.geo_charts import (
        create_city_cluster_map,
        create_city_heatmap_layer,
        create_jobs_distribution_map_enhanced,
    )

    __all__ = [
        "CuratedDataset",
        "CuratedDatasetReader",
        "JoinedObservationRecord",
        "MetricsBuildResult",
        "build_report_metrics",
        "resolve_closed_period",
        "resolve_reference_date",
        "create_all_charts",
        "create_employment_type_chart",
        "create_industry_distribution_chart",
        "create_jobs_distribution_map",
        "create_remote_distribution_chart",
        "create_seniority_distribution_chart",
        "create_tech_stack_overview_heatmap",
        "create_top_cities_chart",
        "create_top_companies_chart",
        "create_top_tech_stack_chart",
        "create_word_cloud_text",
        "figure_to_base64_png",
        "create_city_heatmap_layer",
        "create_city_cluster_map",
        "create_jobs_distribution_map_enhanced",
    ]
except ImportError:
    # Plotly not installed, charts not available
    __all__ = [
        "CuratedDataset",
        "CuratedDatasetReader",
        "JoinedObservationRecord",
        "MetricsBuildResult",
        "build_report_metrics",
        "resolve_closed_period",
        "resolve_reference_date",
    ]
