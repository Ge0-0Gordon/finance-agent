from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import EventAnalysis, EventRecord, ResearchRunRequest, SourceDocument


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
    ) -> tuple[str, str]:
        analysis_by_event = {item.event_id: item for item in analyses}
        context = {
            "request": request,
            "sources": sources,
            "events": events,
            "analysis_by_event": analysis_by_event,
            "warnings": warnings,
            "generated_at": datetime.now(timezone.utc),
            "is_replay": request.mode.value == "replay",
        }
        markdown_text = self.environment.get_template("report.md.j2").render(**context)
        body = markdown.markdown(markdown_text, extensions=["tables", "fenced_code"])
        html_text = self.environment.get_template("report.html.j2").render(
            content=body,
            title=f"AI Finance Research Report — {request.topic}",
            is_replay=context["is_replay"],
        )
        return markdown_text, html_text

