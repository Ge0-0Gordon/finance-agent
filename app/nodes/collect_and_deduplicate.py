from __future__ import annotations

from app.config import Settings
from app.models import RunMode
from app.tools.deduplicate import deduplicate_documents
from app.tools.replay import load_replay_documents
from app.tools.rss import collect_rss_documents
from app.workflow_state import WorkflowState


class CollectAndDeduplicateNode:
    def __init__(self, settings: Settings, observer) -> None:
        self.settings = settings
        self.observer = observer

    def __call__(self, state: WorkflowState) -> dict:
        request = state["request"]
        self.observer("collect", {"status": "running"})
        if request.mode == RunMode.REPLAY:
            raw_documents, warnings = load_replay_documents(self.settings.replay_file, request)
        else:
            raw_documents, warnings = collect_rss_documents(
                self.settings.load_sources(),
                request,
            )
        documents = deduplicate_documents(raw_documents)
        if not documents:
            raise ValueError("No source documents remained after collection and deduplication")
        metrics = {
            "collected_count": len(raw_documents),
            "deduplicated_count": len(documents),
        }
        self.observer("collect", {"status": "completed", **metrics})
        return {"sources": documents, "warnings": warnings, "metrics": metrics}

