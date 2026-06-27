from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.models import Confidence, EventAnalysis, ResearchRunRequest


def test_request_rejects_invalid_time_range():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        ResearchRunRequest(topic="AI", start_time=now, end_time=now - timedelta(hours=1))


def test_request_rejects_too_few_events():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        ResearchRunRequest(
            topic="AI",
            start_time=now - timedelta(days=1),
            end_time=now,
            max_events=4,
        )


def test_external_assumptions_require_explicit_label():
    with pytest.raises(ValidationError, match="外部常识/待验证假设"):
        EventAnalysis(
            event_id="E001",
            tech_product_summary="技术",
            securities_impact="影响",
            quant_impact="量化",
            opportunities=[],
            risks=[],
            recommendations=[],
            external_assumptions=["SEC 规则需要单独核实"],
            confidence=Confidence.LOW,
            confidence_reason="测试",
            evidence_ids=["S001"],
        )
