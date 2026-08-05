"""Committed per-period narrative cache.

The compute stays stateless: every run rebuilds the DuckDB from the full upstream
history and regenerates every closed period. The one thing that cannot be reproduced
deterministically is the LLM narrative, so it is cached here per period, keyed by a
content hash of that period's aggregate metrics. A period is narrated once and reused
on every later run; only genuinely new or changed periods reach the wrapped client and
its provider call. This is what lets the archive be rebuilt from source each week without
ever being overwritten, and without paying to re-narrate history.

Entries are namespaced by narration provider, so switching providers narrates the period
again instead of republishing the other provider's text, and switching back is not
destructive. The namespace stops at the provider: within one provider a model change
reuses the cached narrative for periods already narrated, and only new periods use the
new model. Comparing two models of the same provider on one period needs a manual clear
of that period's cache file.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from mexico_linkedin_jobs_portfolio.models import GeneratedNarrative, ReportMetrics
from mexico_linkedin_jobs_portfolio.reporting.openai_narration import NarrationClient

# Every pre-namespace cache entry was narrated by the then-only provider. Spelled out
# here rather than imported from the config package, which would import this module back.
LEGACY_CACHE_PROVIDER = "openai"


def metrics_cache_key(metrics: ReportMetrics) -> str:
    """Return a stable hash of the narrative-relevant metrics.

    The run-varying ``reference_date`` is excluded so the same period hashes identically
    across runs regardless of the as-of date used to select it.
    """

    payload = metrics.narrative_payload()
    payload.pop("reference_date", None)
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def narrative_to_dict(narrative: GeneratedNarrative) -> dict[str, object]:
    """Serialize a narrative for the cache file."""

    return asdict(narrative)


def narrative_from_dict(payload: dict[str, object]) -> GeneratedNarrative:
    """Rebuild a narrative from its cached representation."""

    return GeneratedNarrative(
        model=str(payload["model"]),
        en_headline=str(payload["en_headline"]),
        en_bullets=tuple(str(item) for item in payload.get("en_bullets", [])),
        es_headline=str(payload["es_headline"]),
        es_bullets=tuple(str(item) for item in payload.get("es_bullets", [])),
    )


def read_cached_narrative(path: Path, key: str) -> GeneratedNarrative | None:
    """Return the cached narrative at ``path`` when it matches ``key``."""

    if not path.is_file():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(cached, dict) or cached.get("metrics_hash") != key:
        return None
    return narrative_from_dict(dict(cached["narrative"]))


@dataclass
class CachingNarrationClient:
    """Wrap a narration client with a committed per-period cache."""

    inner: NarrationClient
    cache_root: Path
    provider: str
    hits: int = field(default=0)
    misses: int = field(default=0)

    def cache_path(self, metrics: ReportMetrics) -> Path:
        """Return the provider-namespaced cache file for one period."""

        return (
            self.cache_root
            / self.provider
            / metrics.period.cadence
            / f"{metrics.period.period_id}.json"
        )

    def legacy_cache_path(self, metrics: ReportMetrics) -> Path:
        """Return the pre-namespace cache file for one period."""

        return self.cache_root / metrics.period.cadence / f"{metrics.period.period_id}.json"

    def generate_bilingual_narrative(self, metrics: ReportMetrics) -> GeneratedNarrative:
        key = metrics_cache_key(metrics)
        path = self.cache_path(metrics)
        candidates = [path]
        # Entries written before the provider namespace existed were narrated by the
        # default provider, so only that provider reads through to them. Reading them
        # under any other provider is what this namespace exists to prevent.
        if self.provider == LEGACY_CACHE_PROVIDER:
            candidates.append(self.legacy_cache_path(metrics))
        for candidate in candidates:
            cached = read_cached_narrative(candidate, key)
            if cached is not None:
                self.hits += 1
                return cached

        narrative = self.inner.generate_bilingual_narrative(metrics)
        self.misses += 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"metrics_hash": key, "narrative": narrative_to_dict(narrative)},
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return narrative
