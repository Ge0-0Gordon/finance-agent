from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.models import ReportArtifacts
from app.reports.renderer import ReportRenderer
from app.workflow_state import WorkflowState


class ReportWriterNode:
    def __init__(self, settings: Settings, observer) -> None:
        self.observer = observer
        self.renderer = ReportRenderer(settings.project_root / "app" / "reports" / "templates")

    def __call__(self, state: WorkflowState) -> dict:
        self.observer("report", {"status": "running"})
        run_dir = Path(state["run_dir"])
        run_dir.mkdir(parents=True, exist_ok=True)
        markdown_text, html_text = self.renderer.render(
            state["request"],
            state["sources"],
            state["events"],
            state["analyses"],
            state.get("warnings", []),
        )

        markdown_path = run_dir / "report.md"
        html_path = run_dir / "report.html"
        json_path = run_dir / "result.json"
        markdown_path.write_text(markdown_text, encoding="utf-8")
        html_path.write_text(html_text, encoding="utf-8")
        json_path.write_text(
            json.dumps(
                {
                    "run_id": state["run_id"],
                    "request": state["request"].model_dump(mode="json"),
                    "sources": [item.model_dump(mode="json") for item in state["sources"]],
                    "events": [item.model_dump(mode="json") for item in state["events"]],
                    "analyses": [item.model_dump(mode="json") for item in state["analyses"]],
                    "warnings": state.get("warnings", []),
                    "metrics": state.get("metrics", {}),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        artifacts = ReportArtifacts(
            result_json_path=str(json_path.resolve()),
            markdown_report_path=str(markdown_path.resolve()),
            html_report_path=str(html_path.resolve()),
        )
        self.observer("report", {"status": "completed"})
        return {"artifacts": artifacts}

