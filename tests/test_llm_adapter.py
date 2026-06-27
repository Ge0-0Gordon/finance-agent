from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

from app.config import Settings
from app.llm_adapter import OpenAICompatibleAdapter
from app.models import Confidence, EventRecord, SourceDocument


class _UnsupportedStructuredOutput:
    def invoke(self, prompt):
        del prompt
        raise NotImplementedError("structured output is not supported")


class _FakeModel:
    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)
        self.fallback_calls = 0

    def with_structured_output(self, schema):
        del schema
        return _UnsupportedStructuredOutput()

    def invoke(self, prompt):
        assert "JSON Schema" in prompt
        self.fallback_calls += 1
        return SimpleNamespace(content=next(self.responses))


def _source() -> SourceDocument:
    return SourceDocument(
        evidence_id="S001",
        title="Synthetic AI event",
        summary="Synthetic evidence",
        url="https://demo.local/event",
        source_name="Demo",
        published_at=datetime.now(timezone.utc),
        source_type="replay",
        metadata={"event_key": "demo"},
    )


def test_openai_compatible_adapter_initializes_with_placeholder_config():
    settings = Settings(
        llm_model="deepseek-v3",
        llm_base_url="https://workspace-placeholder.example.invalid/compatible-mode/v1",
        llm_api_key="placeholder-not-a-real-key",
        llm_temperature=0,
    )

    adapter = OpenAICompatibleAdapter(settings)

    assert adapter.model.model_name == "deepseek-v3"


def test_event_extractor_falls_back_to_json_and_retries_once():
    valid = {
        "events": [
            {
                "event_id": "E001",
                "title": "Synthetic event",
                "event_type": "demo",
                "summary": "Summary",
                "entities": ["Demo"],
                "importance_score": 80,
                "evidence_ids": ["S001"],
            }
        ]
    }
    model = _FakeModel(["not json", json.dumps(valid)])
    adapter = OpenAICompatibleAdapter(Settings(), model=model)

    events = adapter.extract_events("AI", [_source()], 5)

    assert events[0].event_id == "E001"
    assert model.fallback_calls == 2


def test_event_analysis_falls_back_to_validated_json():
    valid = {
        "event_id": "E001",
        "tech_product_summary": "Tech",
        "securities_impact": "Securities",
        "quant_impact": "Quant",
        "opportunities": ["Opportunity"],
        "risks": ["Risk"],
        "recommendations": ["Validate"],
        "confidence": "medium",
        "confidence_reason": "One source",
        "evidence_ids": ["S001"],
    }
    model = _FakeModel([f"```json\n{json.dumps(valid)}\n```"])
    adapter = OpenAICompatibleAdapter(Settings(), model=model)
    event = EventRecord(
        event_id="E001",
        title="Synthetic event",
        event_type="demo",
        summary="Summary",
        importance_score=80,
        evidence_ids=["S001"],
    )

    analysis = adapter.analyze_event(event, [_source()])

    assert analysis.confidence == Confidence.MEDIUM
    assert analysis.evidence_ids == ["S001"]
