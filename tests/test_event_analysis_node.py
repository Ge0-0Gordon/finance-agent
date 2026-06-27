from datetime import datetime, timezone

import pytest

from app.models import Confidence, EventAnalysis, EventRecord, RunMode, SourceDocument
from app.nodes.event_analysis import (
    apply_confidence_policy,
    label_external_framework_usage,
    normalize_research_language,
)


def test_external_framework_is_labeled_when_absent_from_evidence():
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

    labeled = label_external_framework_usage(analysis, event, evidence)

    assert len(labeled.external_assumptions) == 1
    assert labeled.external_assumptions[0].startswith("外部常识/待验证假设：")
    assert "SEC" in labeled.external_assumptions[0]


def test_quant_language_is_rewritten_as_research_hypothesis():
    analysis = EventAnalysis(
        event_id="E001",
        tech_product_summary="技术摘要",
        securities_impact="证券影响",
        quant_impact="可能形成事件驱动型交易机会。",
        opportunities=["该事件可交易。"],
        risks=[],
        recommendations=["可关注某类股票。"],
        external_assumptions=[],
        confidence=Confidence.LOW,
        confidence_reason="测试",
        evidence_ids=["S001"],
    )

    normalized = normalize_research_language(analysis)

    assert "交易机会" not in normalized.quant_impact
    assert "历史事件和市场数据验证" in normalized.quant_impact
    assert normalized.opportunities == ["该事件可作为后续验证假设。"]
    assert normalized.recommendations == ["可将相关行业作为研究观察方向。"]


def test_buy_sell_language_is_rejected():
    analysis = EventAnalysis(
        event_id="E001",
        tech_product_summary="技术摘要",
        securities_impact="证券影响",
        quant_impact="建议 BUY。",
        opportunities=[],
        risks=[],
        recommendations=[],
        external_assumptions=[],
        confidence=Confidence.LOW,
        confidence_reason="测试",
        evidence_ids=["S001"],
    )

    with pytest.raises(ValueError, match="prohibited"):
        normalize_research_language(analysis)


def test_single_source_high_confidence_is_capped_at_medium():
    event = EventRecord(
        event_id="E001",
        title="事件",
        event_type="demo",
        summary="摘要",
        importance_score=80,
        evidence_ids=["S001"],
    )
    analysis = EventAnalysis(
        event_id="E001",
        tech_product_summary="技术",
        securities_impact="证券影响",
        quant_impact="量化影响",
        opportunities=[],
        risks=[],
        recommendations=[],
        confidence=Confidence.HIGH,
        confidence_reason="模型判断较高",
        evidence_ids=["S001"],
    )

    capped = apply_confidence_policy(analysis, event, RunMode.LIVE)

    assert capped.confidence == Confidence.MEDIUM
    assert "只有一个输入来源" in capped.confidence_reason
