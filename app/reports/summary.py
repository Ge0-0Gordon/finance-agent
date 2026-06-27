from __future__ import annotations

import re

from app.models import EventAnalysis, EventRecord, ReportSummary


def _first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[。！？.!?])\s+", text.strip(), maxsplit=1)
    return parts[0] if parts else text.strip()


def _unique(items: list[str], limit: int) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = item.strip()
        if normalized and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
        if len(result) >= limit:
            break
    return result


def build_report_summary(
    events: list[EventRecord],
    analyses: list[EventAnalysis],
) -> ReportSummary:
    """Build a deterministic synthesis using only existing event analyses."""
    if not events:
        raise ValueError("Cannot build report summary without events")
    analysis_by_event = {item.event_id: item for item in analyses}
    ordered_analyses = [analysis_by_event[event.event_id] for event in events]
    leading_titles = "、".join(event.title for event in events[:3])
    executive_summary = (
        f"本次共识别 {len(events)} 个重点事件。按 importance_score 排名靠前的事件为"
        f"{leading_titles}。以下总体判断仅压缩已有 EventAnalysis，不引入额外事实。"
    )
    securities_overview = "；".join(
        _first_sentence(item.securities_impact) for item in ordered_analyses[:3]
    )
    quant_overview = "；".join(
        _first_sentence(item.quant_impact) for item in ordered_analyses[:3]
    )
    return ReportSummary(
        executive_summary=executive_summary,
        securities_overview=securities_overview,
        quant_overview=quant_overview,
        top_opportunities=_unique(
            [value for item in ordered_analyses for value in item.opportunities],
            5,
        ),
        top_risks=_unique(
            [value for item in ordered_analyses for value in item.risks],
            5,
        ),
        priority_recommendations=_unique(
            [value for item in ordered_analyses for value in item.recommendations],
            5,
        ),
    )

