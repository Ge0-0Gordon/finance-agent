from datetime import datetime, timezone

import pytest

from app.models import Confidence, EventAnalysis, EventRecord, SourceDocument
from app.nodes.event_analysis import validate_external_framework_usage


def test_external_framework_must_be_declared_when_absent_from_evidence():
    event = EventRecord(
        event_id="E001",
        title="AI Agent",
        event_type="demo",
        summary="输入证据没有外部监管框架。",
        importance_score=80,
        evidence_ids=["S001"],
    )
    evidence = [
        SourceDocument(
            evidence_id="S001",
            title="AI Agent",
            summary="合成输入证据。",
            url="https://demo.local/event",
            source_name="Demo",
            published_at=datetime.now(timezone.utc),
            source_type="replay",
        )
    ]
    analysis = EventAnalysis(
        event_id="E001",
        tech_product_summary="技术摘要",
        securities_impact="可能需要对照 SEC 要求。",
        quant_impact="量化影响",
        opportunities=[],
        risks=[],
        recommendations=[],
        external_assumptions=[],
        confidence=Confidence.LOW,
        confidence_reason="测试",
        evidence_ids=["S001"],
    )

    with pytest.raises(ValueError, match="SEC"):
        validate_external_framework_usage(analysis, event, evidence)

