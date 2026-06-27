from __future__ import annotations

from typing import TypedDict

from app.models import (
    EventAnalysis,
    EventRecord,
    ReportArtifacts,
    ResearchRunRequest,
    SourceDocument,
)


class WorkflowState(TypedDict, total=False):
    run_id: str
    run_dir: str
    request: ResearchRunRequest
    sources: list[SourceDocument]
    events: list[EventRecord]
    analyses: list[EventAnalysis]
    artifacts: ReportArtifacts
    warnings: list[str]
    metrics: dict[str, int]

