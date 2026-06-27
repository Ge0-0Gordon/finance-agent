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

