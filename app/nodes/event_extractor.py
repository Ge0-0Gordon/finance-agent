from __future__ import annotations

from app.llm_adapter import AnalysisAdapter
from app.tools.deduplicate import validate_evidence_ids
from app.workflow_state import WorkflowState


class EventExtractorNode:
    def __init__(self, adapter: AnalysisAdapter, observer) -> None:
        self.adapter = adapter
        self.observer = observer

    def __call__(self, state: WorkflowState) -> dict:
        self.observer("extract", {"status": "running"})
        request = state["request"]
        sources = state["sources"]
        events = self.adapter.extract_events(
            request.topic,
            sources,
            request.max_events,
            request.output_language,
        )
        if not events:
            raise ValueError("Event extraction returned no events")
        events = sorted(
            events,
            key=lambda item: item.importance_score,
            reverse=True,
        )[: request.max_events]
        available_ids = {item.evidence_id for item in sources}
        for event in events:
            validate_evidence_ids(
                event.evidence_ids,
                available_ids,
                context=f"Event {event.event_id}",
            )
        self.observer("extract", {"status": "completed", "event_count": len(events)})
        metrics = dict(state.get("metrics", {}))
        metrics["event_count"] = len(events)
        return {"events": events, "metrics": metrics}
