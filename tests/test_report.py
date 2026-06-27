from datetime import datetime, timedelta, timezone

from app.config import PROJECT_ROOT
from app.models import (
    Confidence,
    EventAnalysis,
    EventRecord,
    ResearchRunRequest,
    SourceDocument,
)
from app.reports.renderer import ReportRenderer


def test_report_contains_replay_warning_and_evidence():
    now = datetime.now(timezone.utc)
    request = ResearchRunRequest(
        topic="AI",
        start_time=now - timedelta(days=1),
        end_time=now,
    )
    source = SourceDocument(
        evidence_id="S001",
        title="Synthetic item",
        summary="Summary",
        url="https://demo.local/item",
        source_name="Demo",
        published_at=now,
        source_type="replay",
    )
    event = EventRecord(
        event_id="E001",
        title="Event",
        event_type="demo",
        summary="Summary",
        importance_score=80,
        evidence_ids=["S001"],
    )
    analysis = EventAnalysis(
        event_id="E001",
        tech_product_summary="Tech",
        securities_impact="Securities",
        quant_impact="Quant",
        opportunities=["Opportunity"],
        risks=["Risk"],
        recommendations=["Validate"],
        confidence=Confidence.MEDIUM,
        confidence_reason="One source",
        evidence_ids=["S001"],
    )
    renderer = ReportRenderer(PROJECT_ROOT / "app" / "reports" / "templates")
    markdown_text, html_text = renderer.render(request, [source], [event], [analysis], [])
    assert "Replay Demo Data" in markdown_text
    assert "S001" in markdown_text
    assert "Synthetic Replay Demo" in html_text


def test_report_sorts_events_and_builds_summary_from_analyses():
    now = datetime.now(timezone.utc)
    request = ResearchRunRequest(
        topic="AI",
        start_time=now - timedelta(days=1),
        end_time=now,
    )
    sources = [
        SourceDocument(
            evidence_id=f"S00{index}",
            title=f"Source {index}",
            summary="Summary",
            url=f"https://demo.local/{index}",
            source_name="Demo",
            published_at=now,
            source_type="replay",
        )
        for index in (1, 2)
    ]
    events = [
        EventRecord(
            event_id="E001",
            title="较低优先级事件",
            event_type="demo",
            summary="Summary",
            importance_score=20,
            evidence_ids=["S001"],
        ),
        EventRecord(
            event_id="E002",
            title="最高优先级事件",
            event_type="demo",
            summary="Summary",
            importance_score=90,
            evidence_ids=["S002"],
        ),
    ]
    analyses = [
        EventAnalysis(
            event_id=event.event_id,
            tech_product_summary="技术分析",
            securities_impact=f"{event.title}的证券影响。",
            quant_impact=f"{event.title}的量化影响。",
            opportunities=[f"{event.title}机会"],
            risks=[f"{event.title}风险"],
            recommendations=[f"{event.title}建议"],
            external_assumptions=[],
            confidence=Confidence.MEDIUM,
            confidence_reason="测试",
            evidence_ids=event.evidence_ids,
        )
        for event in events
    ]
    renderer = ReportRenderer(PROJECT_ROOT / "app" / "reports" / "templates")
    markdown_text, _ = renderer.render(request, sources, events, analyses, [])

    overview = markdown_text.split("## 三、事件详细分析", maxsplit=1)[0]
    assert overview.index("最高优先级事件") < overview.index("较低优先级事件")
    assert "最高优先级事件的证券影响" in markdown_text
    assert "最高优先级事件机会" in markdown_text


def test_event_analysis_prompt_requires_external_assumption_label():
    prompt = (PROJECT_ROOT / "app" / "prompts" / "event_analysis.md").read_text(
        encoding="utf-8"
    )
    assert "外部常识/待验证假设：" in prompt
    assert "SEC、FINRA、HIPAA" in prompt
