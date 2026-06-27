from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.llm_adapter import AnalysisAdapter
from app.tools.deduplicate import validate_evidence_ids
from app.workflow_state import WorkflowState


class EventAnalysisNode:
    def __init__(self, adapter: AnalysisAdapter, observer, max_workers: int = 3) -> None:
        self.adapter = adapter
        self.observer = observer
        self.max_workers = max_workers

    def __call__(self, state: WorkflowState) -> dict:
        self.observer("analyze", {"status": "running"})
        sources_by_id = {item.evidence_id: item for item in state["sources"]}

        def analyze(event):
            evidence = [sources_by_id[item] for item in event.evidence_ids]
            analysis = self.adapter.analyze_event(event, evidence)
            if analysis.event_id != event.event_id:
                raise ValueError(
                    f"Analysis event ID {analysis.event_id} does not match {event.event_id}"
                )
            validate_evidence_ids(
                analysis.evidence_ids,
                set(event.evidence_ids),
                context=f"Analysis {event.event_id}",
            )
            return analysis

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            analyses = list(executor.map(analyze, state["events"]))

        self.observer("analyze", {"status": "completed", "analysis_count": len(analyses)})
        return {"analyses": analyses}

