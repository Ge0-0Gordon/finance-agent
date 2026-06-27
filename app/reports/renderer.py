from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import EventAnalysis, EventRecord, ResearchRunRequest, SourceDocument
from app.reports.summary import build_report_summary


class ReportRenderer:
    def __init__(self, template_dir: Path) -> None:
        self.environment = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(("html", "xml")),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(
        self,
        request: ResearchRunRequest,
        sources: list[SourceDocument],
        events: list[EventRecord],
        analyses: list[EventAnalysis],
        warnings: list[str],
        metrics: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        events = sorted(events, key=lambda item: item.importance_score, reverse=True)
        analysis_by_event = {item.event_id: item for item in analyses}
        summary = build_report_summary(events, analyses)
        context = {
            "request": request,
            "sources": sources,
            "events": events,
            "analysis_by_event": analysis_by_event,
            "summary": summary,
            "warnings": warnings,
            "generated_at": datetime.now(timezone.utc),
            "is_replay": request.mode.value in {"replay", "replay_llm"},
            "is_replay_llm": request.mode.value == "replay_llm",
            "is_live": request.mode.value == "live",
            "metrics": metrics or {},
        }
        markdown_text = self.environment.get_template("report.md.j2").render(**context)
        body = markdown.markdown(markdown_text, extensions=["tables", "fenced_code"])
        html_text = self.environment.get_template("report.html.j2").render(
            content=body,
            title=f"AI 金融研究报告 — {request.topic}",
            is_replay=context["is_replay"],
        )
        return markdown_text, html_text
