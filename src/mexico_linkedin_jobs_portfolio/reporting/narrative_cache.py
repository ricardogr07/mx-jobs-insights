"""Committed per-period narrative cache.

The compute stays stateless: every run rebuilds the DuckDB from the full upstream
history and regenerates every closed period. The one thing that cannot be reproduced
deterministically is the LLM narrative, so it is cached here per period, keyed by a
content hash of that period's aggregate metrics. A period is narrated once and reused
on every later run; only genuinely new or changed periods reach the wrapped client and
its OpenAI call. This is what lets the archive be rebuilt from source each week without
ever being overwritten, and without paying to re-narrate history.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from mexico_linkedin_jobs_portfolio.models import GeneratedNarrative, ReportMetrics
from mexico_linkedin_jobs_portfolio.reporting.openai_narration import NarrationClient


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


@dataclass
class CachingNarrationClient:
    """Wrap a narration client with a committed per-period cache."""

    inner: NarrationClient
    cache_root: Path
    hits: int = field(default=0)
    misses: int = field(default=0)

    def generate_bilingual_narrative(self, metrics: ReportMetrics) -> GeneratedNarrative:
        key = metrics_cache_key(metrics)
        path = self.cache_root / metrics.period.cadence / f"{metrics.period.period_id}.json"
        if path.is_file():
            try:
                cached = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                cached = None
            if isinstance(cached, dict) and cached.get("metrics_hash") == key:
                self.hits += 1
                return narrative_from_dict(dict(cached["narrative"]))

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
