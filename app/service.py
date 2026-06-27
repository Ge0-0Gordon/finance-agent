from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import Settings
from app.llm_adapter import AnalysisAdapter, OpenAICompatibleAdapter, ReplayAnalysisAdapter
from app.models import ResearchRunRequest, ResearchRunResult, RunMode
from app.workflow import build_workflow


Observer = Callable[[str, dict], None]
AdapterFactory = Callable[[Settings], AnalysisAdapter]


def _noop_observer(stage: str, payload: dict) -> None:
    del stage, payload


class ResearchService:
    def __init__(
        self,
        settings: Settings | None = None,
        llm_adapter_factory: AdapterFactory | None = None,
    ) -> None:
        self.settings = settings or Settings.load()
        self.llm_adapter_factory = llm_adapter_factory or OpenAICompatibleAdapter

    def run(
        self,
        request: ResearchRunRequest,
        observer: Observer | None = None,
    ) -> ResearchRunResult:
        callback = observer or _noop_observer
        adapter = (
            ReplayAnalysisAdapter()
            if request.mode == RunMode.REPLAY
            else self.llm_adapter_factory(self.settings)
        )
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"{timestamp}-{uuid4().hex[:8]}"
        run_dir = Path(self.settings.output_dir) / run_id
        graph = build_workflow(self.settings, adapter, callback)
        final_state = graph.invoke(
            {
                "run_id": run_id,
                "run_dir": str(run_dir),
                "request": request,
                "warnings": [],
                "metrics": {},
            }
        )
        result = ResearchRunResult(
            run_id=run_id,
            request=request,
            sources=final_state["sources"],
            events=final_state["events"],
            analyses=final_state["analyses"],
            artifacts=final_state["artifacts"],
            warnings=final_state.get("warnings", []),
            metrics=final_state.get("metrics", {}),
        )
        Path(result.artifacts.result_json_path).write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return result
