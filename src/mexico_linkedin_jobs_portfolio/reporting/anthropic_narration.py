"""Anthropic-backed narrative generation from aggregate report metrics only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request

from mexico_linkedin_jobs_portfolio.models import GeneratedNarrative, ReportMetrics
from mexico_linkedin_jobs_portfolio.reporting.openai_narration import (
    _NARRATIVE_SCHEMA,
    _SYSTEM_PROMPT,
    build_mock_narrative,
)

ANTHROPIC_VERSION = "2023-06-01"

# The bilingual payload is short and fully specified by the schema, so the response
# needs no reasoning headroom. max_tokens caps thinking plus response text together.
NARRATION_MAX_TOKENS = 2048

NARRATIVE_BULLET_COUNT = 3

# The OpenAI schema carries the exact bullet count in minItems/maxItems, which is
# stripped below because Anthropic rejects it. Nothing else in the shared system
# prompt states the count, so without this the model is never told the requirement
# and only finds out by being rejected on parse.
_BULLET_COUNT_INSTRUCTION = (
    f"Each locale must contain exactly {NARRATIVE_BULLET_COUNT} bullets, no more and no fewer."
)

_UNSUPPORTED_SCHEMA_KEYS = frozenset({"minItems", "maxItems"})


def _strip_unsupported_schema_keys(node: object) -> object:
    """Drop JSON Schema keywords the Anthropic structured-output validator rejects.

    Anthropic only accepts `minItems` values of 0 or 1, so the exact-count
    constraint the OpenAI schema uses is a hard 400 here. The OpenAI client keeps
    the strict schema; this request drops the bounds and the count is enforced on
    parse instead, in `_extract_narrative_payload`.
    """

    if isinstance(node, dict):
        return {
            key: _strip_unsupported_schema_keys(value)
            for key, value in node.items()
            if key not in _UNSUPPORTED_SCHEMA_KEYS
        }
    if isinstance(node, list):
        return [_strip_unsupported_schema_keys(item) for item in node]
    return node


@dataclass(frozen=True, slots=True)
class AnthropicNarrationClient:
    """Minimal Messages API client used by the reporting pipeline."""

    api_key: str
    model: str
    base_url: str = "https://api.anthropic.com/v1"

    def generate_bilingual_narrative(self, metrics: ReportMetrics) -> GeneratedNarrative:
        if self.base_url.startswith("mock://"):
            return build_mock_narrative(metrics, self.model)

        body = build_anthropic_narration_request_body(metrics, self.model)
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
        endpoint = self.base_url.rstrip("/") + "/messages"
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Anthropic Messages API request failed: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Anthropic Messages API request failed: {exc.reason}") from exc
        except OSError as exc:
            raise RuntimeError(f"Anthropic Messages API request failed: {exc}") from exc


def build_anthropic_narration_request_body(metrics: ReportMetrics, model: str) -> dict[str, object]:
    """Build the aggregate-only Messages API request body."""

    return {
        "model": model,
        "max_tokens": NARRATION_MAX_TOKENS,
        "system": _SYSTEM_PROMPT + " " + _BULLET_COUNT_INSTRUCTION,
        "thinking": {"type": "disabled"},
        "messages": [
            {
                "role": "user",
                "content": (
                    "Aggregate metrics JSON for the selected report period:\n"
                    + json.dumps(
                        metrics.narrative_payload(),
                        ensure_ascii=False,
                        sort_keys=True,
                        indent=2,
                    )
                ),
            }
        ],
        "output_config": {
            "format": {
                "type": "json_schema",
                "schema": _strip_unsupported_schema_keys(_NARRATIVE_SCHEMA),
            }
        },
    }


def _extract_narrative_payload(response_payload: dict[str, object]) -> dict[str, object]:
    if response_payload.get("error"):
        raise RuntimeError(f"Anthropic Messages API returned an error: {response_payload['error']}")

    stop_reason = response_payload.get("stop_reason")
    if stop_reason == "refusal":
        raise RuntimeError(
            f"Anthropic narrative request was refused: {response_payload.get('stop_details')}"
        )

    texts: list[str] = []
    for content_block in response_payload.get("content", []):
        if not isinstance(content_block, dict):
            continue
        if content_block.get("type") == "text":
            texts.append(str(content_block.get("text") or ""))

    if not texts:
        raise RuntimeError("Anthropic Messages API returned no text content.")

    try:
        narrative = json.loads("".join(texts))
    except json.JSONDecodeError as exc:
        raise RuntimeError("Anthropic narrative response was not valid JSON.") from exc
    if not isinstance(narrative, dict):
        raise RuntimeError("Anthropic narrative response did not match the expected JSON object.")

    for locale in ("en", "es"):
        section = narrative.get(locale)
        if not isinstance(section, dict):
            raise RuntimeError(f"Anthropic narrative response is missing the {locale} section.")
        bullets = section.get("bullets")
        if not isinstance(bullets, list) or len(bullets) != NARRATIVE_BULLET_COUNT:
            raise RuntimeError(
                f"Anthropic narrative {locale} bullets must be a list of "
                f"{NARRATIVE_BULLET_COUNT} items."
            )

    return narrative
