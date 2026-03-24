"""OpenAI-backed narrative generation from aggregate report metrics only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib import error, request

from mexico_linkedin_jobs_portfolio.models import GeneratedNarrative, ReportMetrics

_NARRATIVE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "en": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "headline": {"type": "string"},
                "bullets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 3,
                },
            },
            "required": ["headline", "bullets"],
        },
        "es": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "headline": {"type": "string"},
                "bullets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 3,
                },
            },
            "required": ["headline", "bullets"],
        },
    },
    "required": ["en", "es"],
}

_SYSTEM_PROMPT = (
    "You are writing a bilingual Mexico jobs analytics report. "
    "Use only the aggregate metrics provided by the user. "
    "Do not invent raw jobs, URLs, descriptions, or row-level identifiers. "
    "Company names may be mentioned only if they already appear in the aggregated "
    "top_company_counts metric. "
    "Return concise JSON matching the provided schema. "
    "If the period has zero jobs, explicitly say so in both locales."
)


class NarrationClient(Protocol):
    """Contract for bilingual narrative generation."""

    def generate_bilingual_narrative(self, metrics: ReportMetrics) -> GeneratedNarrative:
        """Return narrative text generated from aggregate metrics only."""


@dataclass(frozen=True, slots=True)
class OpenAINarrationClient:
    """Minimal Responses API client used by the reporting pipeline."""

    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1"

    def generate_bilingual_narrative(self, metrics: ReportMetrics) -> GeneratedNarrative:
        if self.base_url.startswith("mock://"):
            return build_mock_narrative(metrics, self.model)

        body = build_narration_request_body(metrics, self.model)
        response_payload = self._post_json(body)
        narrative = _extract_narrative_payload(response_payload)
        return GeneratedNarrative(
            model=str(response_payload.get("model") or self.model),
            en_headline=str(narrative["en"]["headline"]),
            en_bullets=tuple(str(item) for item in narrative["en"]["bullets"]),
            es_headline=str(narrative["es"]["headline"]),
            es_bullets=tuple(str(item) for item in narrative["es"]["bullets"]),
        )

    def _post_json(self, payload: dict[str, object]) -> dict[str, object]:
        endpoint = self.base_url.rstrip("/") + "/responses"
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI Responses API request failed: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenAI Responses API request failed: {exc.reason}") from exc
        except OSError as exc:
            raise RuntimeError(f"OpenAI Responses API request failed: {exc}") from exc


def build_narration_request_body(metrics: ReportMetrics, model: str) -> dict[str, object]:
    """Build the aggregate-only Responses API request body."""

    return {
        "model": model,
        "instructions": _SYSTEM_PROMPT,
        "input": (
            "Aggregate metrics JSON for the selected report period:\n"
            + json.dumps(metrics.narrative_payload(), ensure_ascii=False, sort_keys=True, indent=2)
        ),
        "store": False,
        "temperature": 0.2,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "bilingual_report_narrative",
                "schema": _NARRATIVE_SCHEMA,
                "strict": True,
            }
        },
    }


def build_mock_narrative(metrics: ReportMetrics, model: str) -> GeneratedNarrative:
    """Return a deterministic local narrative for offline validation."""

    if metrics.job_count == 0:
        return GeneratedNarrative(
            model=model,
            en_headline=f"No jobs were observed for {metrics.period.label}.",
            en_bullets=(
                "No curated job observations fell inside this closed period.",
                "The public CSV is empty for this report window.",
                "A later closed period with observations will repopulate the metrics.",
            ),
            es_headline=f"No se observaron vacantes en {metrics.period.label}.",
            es_bullets=(
                "No hubo observaciones curadas dentro de este periodo cerrado.",
                "El CSV publico queda vacio para esta ventana del reporte.",
                "Un periodo cerrado posterior con observaciones volvera a poblar las metricas.",
            ),
        )

    top_city = _top_label(metrics.city_counts)
    top_remote = _top_label(metrics.remote_type_counts)
    top_tech = _top_label(metrics.tech_stack_counts)

    return GeneratedNarrative(
        model=model,
        en_headline=(
            f"{metrics.job_count} distinct jobs were observed during {metrics.period.label}."
        ),
        en_bullets=(
            f"{metrics.observation_count} observations were captured across {metrics.source_run_count} source runs.",
            _format_insight(
                top_city,
                "{label} led the visible city mix.",
                "No city concentration signal was available in the aggregate metrics.",
            ),
            _format_insight(
                top_tech or top_remote,
                "{label} stood out in the aggregate breakdown.",
                "No standout tech-stack or remote-work label was available in the aggregate metrics.",
            ),
        ),
        es_headline=(
            f"Se observaron {metrics.job_count} vacantes distintas durante {metrics.period.label}."
        ),
        es_bullets=(
            f"Se capturaron {metrics.observation_count} observaciones en {metrics.source_run_count} corridas de origen.",
            _format_insight(
                top_city,
                "{label} lidero la mezcla visible por ciudad.",
                "No hubo una senal clara de concentracion por ciudad en las metricas agregadas.",
            ),
            _format_insight(
                top_tech or top_remote,
                "{label} destaco en el desglose agregado.",
                "No hubo una etiqueta destacada de tecnologia o modalidad remota en las metricas agregadas.",
            ),
        ),
    )


def _top_label(counts) -> str | None:
    return counts[0].label if counts else None


def _format_insight(label: str | None, template: str, empty_message: str) -> str:
    if not label:
        return empty_message
    return template.format(label=label)


def _extract_narrative_payload(response_payload: dict[str, object]) -> dict[str, object]:
    if response_payload.get("status") not in {None, "completed"}:
        raise RuntimeError(
            f"OpenAI Responses API returned unexpected status: {response_payload.get('status')}"
        )
    if response_payload.get("error"):
        raise RuntimeError(f"OpenAI Responses API returned an error: {response_payload['error']}")

    texts: list[str] = []
    for output_item in response_payload.get("output", []):
        if not isinstance(output_item, dict) or output_item.get("type") != "message":
            continue
        for content_part in output_item.get("content", []):
            if not isinstance(content_part, dict):
                continue
            if content_part.get("type") == "refusal":
                raise RuntimeError(f"OpenAI narrative request was refused: {content_part.get('refusal')}")
            if content_part.get("type") == "output_text":
                texts.append(str(content_part.get("text") or ""))

    if not texts:
        raise RuntimeError("OpenAI Responses API returned no output_text content.")

    try:
        narrative = json.loads("".join(texts))
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI narrative response was not valid JSON.") from exc
    if not isinstance(narrative, dict):
        raise RuntimeError("OpenAI narrative response did not match the expected JSON object.")
    return narrative
