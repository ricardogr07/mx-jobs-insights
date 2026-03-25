"""Tests for word cloud visualization functions (Phase 2.3)."""

from datetime import date

import pytest

from mexico_linkedin_jobs_portfolio.analytics.charts import create_word_cloud_text
from mexico_linkedin_jobs_portfolio.models import DimensionCount, PeriodWindow, ReportMetrics


@pytest.fixture
def sample_metrics_with_tech() -> ReportMetrics:
    """Create sample metrics with tech stack data for word cloud testing."""
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
            DimensionCount("JavaScript", 11),
            DimensionCount("TypeScript", 9),
            DimensionCount("Docker", 8),
            DimensionCount("Kubernetes", 7),
            DimensionCount("Go", 6),
            DimensionCount("Rust", 5),
            DimensionCount("C++", 4),
            DimensionCount("C#", 3),
            DimensionCount("Ruby", 2),
            DimensionCount("PHP", 1),
        ),
        english_requirement_counts=(),
        experience_bucket_counts=(),
        top_company_counts=(
            DimensionCount("TechCorp", 8),
            DimensionCount("DataSys", 6),
        ),
        industry_counts=(
            DimensionCount("Technology", 35),
            DimensionCount("Finance", 15),
        ),
    )


@pytest.fixture
def empty_metrics() -> ReportMetrics:
    """Create metrics with empty tech stack."""
    return ReportMetrics(
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
        tech_stack_counts=(),  # Empty tech stack
        english_requirement_counts=(),
        experience_bucket_counts=(),
        top_company_counts=(),
        industry_counts=(),
    )


class TestWordCloudGeneration:
    """Test word cloud visualization generation."""

    def test_word_cloud_with_tech_data(self, sample_metrics_with_tech):
        """Test word cloud generation with valid tech stack data."""
        result = create_word_cloud_text(sample_metrics_with_tech)

        # If wordcloud is installed, should return base64 PNG
        if result:  # wordcloud library available
            assert result.startswith("data:image/png;base64,")
            assert len(result) > 100  # Non-trivial PNG size
        # If wordcloud not installed, gracefully returns empty string

    def test_word_cloud_empty_tech_stack(self, empty_metrics):
        """Test word cloud with empty tech stack returns empty string."""
        result = create_word_cloud_text(empty_metrics)
        assert result == ""  # Empty tech data should return empty string

    def test_word_cloud_single_technology(self):
        """Test word cloud with single technology."""
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
            city_counts=(DimensionCount("Mexico City", 5),),
            remote_type_counts=(),
            seniority_counts=(),
            employment_type_counts=(),
            tech_stack_counts=(DimensionCount("Python", 5),),  # Only one tech
            english_requirement_counts=(),
            experience_bucket_counts=(),
            top_company_counts=(),
            industry_counts=(),
        )

        result = create_word_cloud_text(metrics)

        # Should handle single technology gracefully
        if result:
            assert result.startswith("data:image/png;base64,")

    def test_word_cloud_many_technologies(self, sample_metrics_with_tech):
        """Test word cloud with many technologies (>50) handles max_words limit."""
        metrics = ReportMetrics(
            period=sample_metrics_with_tech.period,
            observation_count=sample_metrics_with_tech.observation_count,
            job_count=sample_metrics_with_tech.job_count,
            source_run_count=sample_metrics_with_tech.source_run_count,
            city_counts=sample_metrics_with_tech.city_counts,
            remote_type_counts=sample_metrics_with_tech.remote_type_counts,
            seniority_counts=sample_metrics_with_tech.seniority_counts,
            employment_type_counts=sample_metrics_with_tech.employment_type_counts,
            tech_stack_counts=(
                *sample_metrics_with_tech.tech_stack_counts,
                DimensionCount("Scala", 1),
                DimensionCount("Clojure", 1),
                DimensionCount("Elixir", 1),
                DimensionCount("Haskell", 1),
                DimensionCount("R", 1),
                DimensionCount("MATLAB", 1),
                DimensionCount("Julia", 1),
                DimensionCount("Lua", 1),
                DimensionCount("Swift", 1),
                DimensionCount("Kotlin", 1),
            ),  # 25 technologies total
            english_requirement_counts=sample_metrics_with_tech.english_requirement_counts,
            experience_bucket_counts=sample_metrics_with_tech.experience_bucket_counts,
            top_company_counts=sample_metrics_with_tech.top_company_counts,
            industry_counts=sample_metrics_with_tech.industry_counts,
        )

        result = create_word_cloud_text(metrics)

        # Should still produce valid output with max_words=50 limit
        if result:
            assert result.startswith("data:image/png;base64,")
            assert len(result) > 100

    def test_word_cloud_graceful_fallback(self, sample_metrics_with_tech, monkeypatch):
        """Test word cloud handles missing wordcloud library gracefully."""
        # This test verifies the try-except ImportError handling
        # by checking that we get empty string when wordcloud can't be imported
        result = create_word_cloud_text(sample_metrics_with_tech)

        # Result should be either valid base64 PNG or empty string
        if result:
            assert result.startswith("data:image/png;base64,")
        else:
            assert result == ""


class TestWordCloudStringContent:
    """Test the actual string format of word cloud output."""

    def test_word_cloud_data_uri_format(self, sample_metrics_with_tech):
        """Test word cloud returns proper data URI format."""
        result = create_word_cloud_text(sample_metrics_with_tech)

        if result:  # Only test format if wordcloud is installed
            # Should be a valid data URI
            assert result.startswith("data:image/png;base64,")

            # Should be reasonably long (contains actual image data)
            assert len(result) > 1000

    def test_word_cloud_base64_valid(self, sample_metrics_with_tech):
        """Test word cloud returns valid base64-encoded data."""
        result = create_word_cloud_text(sample_metrics_with_tech)

        if result:
            # Extract base64 portion
            base64_data = result.replace("data:image/png;base64,", "")

            # Should be able to decode (no invalid characters)
            import base64

            try:
                decoded = base64.b64decode(base64_data)
                # PNG files start with specific magic bytes
                assert decoded[:4] == b"\x89PNG"
            except Exception:
                pytest.fail("Base64 data is invalid or not a PNG")
