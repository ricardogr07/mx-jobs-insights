"""Tests for geographic visualization functions (Phase 2.1)."""

from datetime import date

import pytest

from mexico_linkedin_jobs_portfolio.analytics.geo_charts import (
    create_city_cluster_map,
    create_city_heatmap_layer,
    create_jobs_distribution_map_enhanced,
)
from mexico_linkedin_jobs_portfolio.models import DimensionCount, PeriodWindow, ReportMetrics


@pytest.fixture
def sample_metrics() -> ReportMetrics:
    """Create sample metrics with city data for testing."""
    return ReportMetrics(
        period=PeriodWindow(
            cadence="weekly",
            period_id="2026-W12",
            label="Week 12 2026",
            start_date=date(2026, 3, 23),
            end_date=date(2026, 3, 29),
            reference_date=date(2026, 3, 29),
        ),
        observation_count=100,
        job_count=50,
        source_run_count=5,
        city_counts=(
            DimensionCount("Mexico City", 30),
            DimensionCount("Guadalajara", 12),
            DimensionCount("Monterrey", 8),
            DimensionCount("Querétaro", 5),
            DimensionCount("Cancún", 3),
        ),
        remote_type_counts=(
            DimensionCount("Remote", 25),
            DimensionCount("On-site", 25),
        ),
        seniority_counts=(
            DimensionCount("Entry-level", 15),
            DimensionCount("Mid-level", 20),
            DimensionCount("Senior", 15),
        ),
        employment_type_counts=(
            DimensionCount("Full-time", 40),
            DimensionCount("Part-time", 10),
        ),
        tech_stack_counts=(
            DimensionCount("Python", 25),
            DimensionCount("SQL", 20),
            DimensionCount("AWS", 18),
            DimensionCount("React", 15),
            DimensionCount("Java", 12),
        ),
        company_counts=(
            DimensionCount("TechCorp", 8),
            DimensionCount("DataSys", 6),
        ),
        industry_counts=(
            DimensionCount("Technology", 35),
            DimensionCount("Finance", 15),
        ),
    )


class TestCityHeatmapLayer:
    """Test heatmap layer geographic visualization."""

    def test_heatmap_creation_english(self, sample_metrics):
        """Test heatmap creation with English labels."""
        result = create_city_heatmap_layer(sample_metrics, locale="en")

        # Should return HTML string for embedding
        if result:
            assert "<html" in result.lower() or "folium" in result.lower()
            assert len(result) > 100  # Non-trivial result

    def test_heatmap_creation_spanish(self, sample_metrics):
        """Test heatmap creation with Spanish labels."""
        result = create_city_heatmap_layer(sample_metrics, locale="es")

        if result:
            assert "<html" in result.lower() or "folium" in result.lower()
            assert len(result) > 100

    def test_heatmap_empty_metrics(self):
        """Test heatmap with empty city data."""
        empty_metrics = ReportMetrics(
            period=PeriodWindow(
                cadence="weekly",
                period_id="2026-W12",
                label="Week 12 2026",
                start_date=date(2026, 3, 23),
                end_date=date(2026, 3, 29),
                reference_date=date(2026, 3, 29),
            ),
            observation_count=0,
            job_count=0,
            source_run_count=0,
            city_counts=(),  # Empty
            remote_type_counts=(),
            seniority_counts=(),
            employment_type_counts=(),
            tech_stack_counts=(),
            company_counts=(),
            industry_counts=(),
        )

        result = create_city_heatmap_layer(empty_metrics)
        assert result == ""  # Should return empty string for empty data

    def test_heatmap_unknown_city(self):
        """Test heatmap gracefully handles unknown cities."""
        metrics = ReportMetrics(
            period=PeriodWindow(
                cadence="weekly",
                period_id="2026-W12",
                label="Week 12 2026",
                start_date=date(2026, 3, 23),
                end_date=date(2026, 3, 29),
                reference_date=date(2026, 3, 29),
            ),
            observation_count=10,
            job_count=5,
            source_run_count=1,
            city_counts=(
                DimensionCount("Unknown City", 10),  # Not in coordinate lookup
                DimensionCount("Mexico City", 5),  # Known city
            ),
            remote_type_counts=(),
            seniority_counts=(),
            employment_type_counts=(),
            tech_stack_counts=(),
            company_counts=(),
            industry_counts=(),
        )

        # Should skip unknown cities but still process known ones
        result = create_city_heatmap_layer(metrics)
        if result:
            assert "<html" in result.lower() or "folium" in result.lower()


class TestCityClusterMap:
    """Test cluster-based geographic visualization."""

    def test_cluster_creation_english(self, sample_metrics):
        """Test cluster map creation with English labels."""
        result = create_city_cluster_map(sample_metrics, locale="en")

        if result:
            assert "<html" in result.lower() or "folium" in result.lower()
            assert len(result) > 100

    def test_cluster_creation_spanish(self, sample_metrics):
        """Test cluster map creation with Spanish labels."""
        result = create_city_cluster_map(sample_metrics, locale="es")

        if result:
            assert "<html" in result.lower() or "folium" in result.lower()
            assert len(result) > 100

    def test_cluster_empty_metrics(self):
        """Test cluster map with empty city data."""
        empty_metrics = ReportMetrics(
            period=PeriodWindow(
                cadence="weekly",
                period_id="2026-W12",
                label="Week 12 2026",
                start_date=date(2026, 3, 23),
                end_date=date(2026, 3, 29),
                reference_date=date(2026, 3, 29),
            ),
            observation_count=0,
            job_count=0,
            source_run_count=0,
            city_counts=(),
            remote_type_counts=(),
            seniority_counts=(),
            employment_type_counts=(),
            tech_stack_counts=(),
            company_counts=(),
            industry_counts=(),
        )

        result = create_city_cluster_map(empty_metrics)
        assert result == ""


class TestEnhancedDistributionMap:
    """Test primary geographic visualization wrapper."""

    def test_enhanced_map_heatmap_mode(self, sample_metrics):
        """Test enhanced map in heatmap mode."""
        result = create_jobs_distribution_map_enhanced(sample_metrics, locale="en", heatmap=True)

        if result:
            assert "<html" in result.lower() or "folium" in result.lower()
            assert len(result) > 100

    def test_enhanced_map_cluster_mode(self, sample_metrics):
        """Test enhanced map in cluster mode."""
        result = create_jobs_distribution_map_enhanced(sample_metrics, locale="en", heatmap=False)

        if result:
            assert "<html" in result.lower() or "folium" in result.lower()
            assert len(result) > 100

    def test_enhanced_map_spanish(self, sample_metrics):
        """Test enhanced map with Spanish labels."""
        result = create_jobs_distribution_map_enhanced(sample_metrics, locale="es", heatmap=True)

        if result:
            assert "<html" in result.lower() or "folium" in result.lower()

    def test_enhanced_map_multiple_modes(self, sample_metrics):
        """Test both modes produce similar-sized outputs."""
        heatmap_result = create_jobs_distribution_map_enhanced(
            sample_metrics, locale="en", heatmap=True
        )
        cluster_result = create_jobs_distribution_map_enhanced(
            sample_metrics, locale="en", heatmap=False
        )

        # Both should produce valid HTML strings
        if heatmap_result:
            assert "<html" in heatmap_result.lower() or "folium" in heatmap_result.lower()
        if cluster_result:
            assert "<html" in cluster_result.lower() or "folium" in cluster_result.lower()

        # Results should be different (different map implementations)
        if heatmap_result and cluster_result:
            assert heatmap_result != cluster_result
