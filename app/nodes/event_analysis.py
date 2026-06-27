from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.llm_adapter import AnalysisAdapter
from app.models import Confidence, RunMode
from app.tools.deduplicate import validate_evidence_ids
from app.workflow_state import WorkflowState


EXTERNAL_FRAMEWORK_TERMS = ("SEC", "FINRA", "HIPAA", "MiFID", "GDPR")


def validate_external_framework_usage(analysis, event, evidence) -> None:
    input_text = " ".join(
        [event.title, event.summary]
        + [item.title for item in evidence]
        + [item.summary for item in evidence]
    )
    analysis_text = " ".join(
        [
            analysis.tech_product_summary,
            analysis.securities_impact,
            analysis.quant_impact,
            *analysis.opportunities,
            *analysis.risks,
            *analysis.recommendations,
        ]
    )
    declared_text = " ".join(analysis.external_assumptions)
    missing = [
        term
        for term in EXTERNAL_FRAMEWORK_TERMS
        if term in analysis_text and term not in input_text and term not in declared_text
    ]
    if missing:
        raise ValueError(
            "Analysis uses external frameworks without declaring them in "
            f"external_assumptions: {missing}"
        )


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
            analysis = self.adapter.analyze_event(
                event,
                evidence,
                state["request"].output_language,
            )
            if analysis.event_id != event.event_id:
                raise ValueError(
                    f"Analysis event ID {analysis.event_id} does not match {event.event_id}"
                )
            validate_evidence_ids(
                analysis.evidence_ids,
                set(event.evidence_ids),
                context=f"Analysis {event.event_id}",
            )
            validate_external_framework_usage(analysis, event, evidence)
            if (
                state["request"].mode in {RunMode.REPLAY, RunMode.REPLAY_LLM}
                and analysis.confidence == Confidence.HIGH
            ):
                analysis = analysis.model_copy(
                    update={
                        "confidence": Confidence.MEDIUM,
                        "confidence_reason": (
                            f"{analysis.confidence_reason} "
                            "该置信度已因使用 synthetic Replay 数据封顶为 medium；"
                            "它只代表输入证据内部一致性，不代表现实真实性。"
                        ),
                    }
                )
            return analysis

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            analyses = list(executor.map(analyze, state["events"]))

        self.observer("analyze", {"status": "completed", "analysis_count": len(analyses)})
        return {"analyses": analyses}
