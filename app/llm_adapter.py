from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Protocol

from langchain_openai import ChatOpenAI

from app.config import Settings
from app.models import (
    Confidence,
    EventAnalysis,
    EventBatch,
    EventRecord,
    SourceDocument,
)


class AnalysisAdapter(Protocol):
    def extract_events(
        self,
        topic: str,
        sources: list[SourceDocument],
        max_events: int,
    ) -> list[EventRecord]: ...

    def analyze_event(
        self,
        event: EventRecord,
        sources: list[SourceDocument],
    ) -> EventAnalysis: ...


class OpenAICompatibleAdapter:
    def __init__(self, settings: Settings) -> None:
        if not settings.llm_api_key:
            raise ValueError("LLM_API_KEY is required in live mode")
        self.model = ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            temperature=settings.llm_temperature,
        )
        prompt_dir = settings.project_root / "app" / "prompts"
        self.extract_prompt = (prompt_dir / "event_extractor.md").read_text(encoding="utf-8")
        self.analysis_prompt = (prompt_dir / "event_analysis.md").read_text(encoding="utf-8")

    def extract_events(
        self,
        topic: str,
        sources: list[SourceDocument],
        max_events: int,
    ) -> list[EventRecord]:
        payload = [item.model_dump(mode="json") for item in sources]
        prompt = self.extract_prompt.format(
            topic=topic,
            max_events=max_events,
            sources_json=json.dumps(payload, ensure_ascii=False),
        )
        result = (
            self.model.with_structured_output(EventBatch)
            .with_retry(stop_after_attempt=2)
            .invoke(prompt)
        )
        return result.events[:max_events]

    def analyze_event(
        self,
        event: EventRecord,
        sources: list[SourceDocument],
    ) -> EventAnalysis:
        prompt = self.analysis_prompt.format(
            event_json=event.model_dump_json(),
            sources_json=json.dumps(
                [item.model_dump(mode="json") for item in sources],
                ensure_ascii=False,
            ),
        )
        return (
            self.model.with_structured_output(EventAnalysis)
            .with_retry(stop_after_attempt=2)
            .invoke(prompt)
        )


_REPLAY_EVENT_INFO = {
    "enterprise-agent": ("Governed enterprise AI agent platform", "product_launch", ["AtlasAI"], 92),
    "inference-chip": ("Lower-cost AI inference accelerator", "infrastructure", ["NovaChip"], 88),
    "financial-benchmark": ("Open benchmark for financial LLMs", "research", ["FinBench"], 84),
    "ai-regulation": ("Model-risk requirements for AI advisory tools", "regulation", ["Market regulator"], 95),
    "point-in-time-data": ("Point-in-time controls for alternative data", "data_infrastructure", ["VectorLake"], 86),
    "agent-security": ("Prompt-injection test suite for finance agents", "security", ["OpenShield"], 93),
    "broker-copilot": ("Citation-first AI copilot for securities research", "industry_adoption", ["BrokerLab"], 89),
}


_REPLAY_ANALYSES = {
    "enterprise-agent": {
        "tech": "The product combines tool permissions, approval gates and auditable execution, shifting enterprise agents from unconstrained assistants toward governed workflow software.",
        "securities": "Brokerages could use governed agents in research and operations where access control and audit evidence are prerequisites, while integration and model-governance work remain material.",
        "quant": "Permissioned tool use may accelerate research orchestration, but generated outputs still require reproducibility checks and separation from production execution.",
        "opportunities": ["Pilot low-risk research workflows with mandatory approval gates."],
        "risks": ["Tool permissions may be misconfigured or bypassed by injected content."],
        "recommendations": ["Evaluate audit completeness and permission isolation before production use."],
    },
    "inference-chip": {
        "tech": "The accelerator targets lower power consumption for transformer inference and may broaden hardware choice beyond incumbent GPU stacks.",
        "securities": "Lower inference costs could improve economics for AI-enabled research and client service, subject to cloud availability and software compatibility.",
        "quant": "Cheaper inference can support more frequent model evaluation, but migration costs and latency under real workloads must be benchmarked.",
        "opportunities": ["Benchmark batch research workloads on alternative inference hardware."],
        "risks": ["Vendor claims may not translate to production price-performance."],
        "recommendations": ["Run workload-specific cost, latency and compatibility tests."],
    },
    "financial-benchmark": {
        "tech": "The benchmark evaluates financial extraction, numerical reasoning, citation accuracy and compliance-sensitive refusal behavior.",
        "securities": "A shared benchmark can improve model procurement and governance by replacing generic leaderboard claims with finance-specific evidence.",
        "quant": "Reproducible tests may help compare research assistants, but benchmark performance does not establish predictive alpha.",
        "opportunities": ["Use the benchmark as one gate in model selection and regression testing."],
        "risks": ["Teams may optimize to benchmark tasks without improving real workflows."],
        "recommendations": ["Combine public scores with internal, time-split evaluation sets."],
    },
    "ai-regulation": {
        "tech": "The proposal centers on documentation, change management, human review and incident escalation rather than a specific model architecture.",
        "securities": "Securities firms may face higher governance and recordkeeping requirements for customer-facing AI advice.",
        "quant": "Internal quantitative research may be indirectly affected through stronger model inventories, validation records and change controls.",
        "opportunities": ["Build reusable model cards, approval records and incident workflows."],
        "risks": ["Compliance requirements may delay deployment or expose undocumented model use."],
        "recommendations": ["Map current AI use cases to proposed documentation and oversight controls."],
    },
    "point-in-time-data": {
        "tech": "Timestamp lineage and dataset revisions make historical data availability explicit.",
        "securities": "Better lineage can strengthen research auditability and vendor governance.",
        "quant": "Point-in-time exports directly address look-ahead bias and improve backtest reproducibility.",
        "opportunities": ["Add availability timestamps and version identifiers to research datasets."],
        "risks": ["Incorrect vendor timestamps can create a false sense of backtest validity."],
        "recommendations": ["Validate timestamp semantics with controlled historical samples."],
    },
    "agent-security": {
        "tech": "The suite tests indirect prompt injection, unsafe tool calls and sensitive-data leakage in agent workflows.",
        "securities": "Financial firms need agent-specific controls before connecting models to research repositories or operational systems.",
        "quant": "Agents that read untrusted documents can contaminate research or trigger unsafe tools unless content and execution boundaries are enforced.",
        "opportunities": ["Add prompt-injection tests to model and agent release gates."],
        "risks": ["Injected source documents may manipulate tools or leak confidential data."],
        "recommendations": ["Isolate tools, restrict credentials and run the red-team suite in CI."],
    },
    "broker-copilot": {
        "tech": "The pilot treats citations and analyst corrections as first-class product metrics.",
        "securities": "Citation-first copilots may reduce research drafting time while preserving reviewer accountability.",
        "quant": "The workflow can speed literature and news review, but it does not replace data validation or signal testing.",
        "opportunities": ["Measure citation coverage, correction rate and time saved in a bounded pilot."],
        "risks": ["Plausible but weak citations may pass superficial review."],
        "recommendations": ["Require source-level review and track correction reasons."],
    },
}


class ReplayAnalysisAdapter:
    """Deterministic adapter for explicitly synthetic offline demonstrations."""

    def extract_events(
        self,
        topic: str,
        sources: list[SourceDocument],
        max_events: int,
    ) -> list[EventRecord]:
        grouped: dict[str, list[SourceDocument]] = defaultdict(list)
        for source in sources:
            grouped[str(source.metadata["event_key"])].append(source)

        events: list[EventRecord] = []
        ordered = sorted(
            grouped.items(),
            key=lambda item: _REPLAY_EVENT_INFO[item[0]][3],
            reverse=True,
        )
        for index, (key, evidence) in enumerate(ordered[:max_events], start=1):
            title, event_type, entities, score = _REPLAY_EVENT_INFO[key]
            events.append(
                EventRecord(
                    event_id=f"E{index:03d}",
                    title=title,
                    event_type=event_type,
                    summary=" ".join(item.summary for item in evidence),
                    entities=entities,
                    importance_score=score,
                    evidence_ids=[item.evidence_id for item in evidence],
                )
            )
        return events

    def analyze_event(
        self,
        event: EventRecord,
        sources: list[SourceDocument],
    ) -> EventAnalysis:
        key = str(sources[0].metadata["event_key"])
        content = _REPLAY_ANALYSES[key]
        confidence = Confidence.HIGH if len(event.evidence_ids) >= 2 else Confidence.MEDIUM
        return EventAnalysis(
            event_id=event.event_id,
            tech_product_summary=content["tech"],
            securities_impact=content["securities"],
            quant_impact=content["quant"],
            opportunities=content["opportunities"],
            risks=content["risks"],
            recommendations=content["recommendations"],
            confidence=confidence,
            confidence_reason=(
                f"Based on {len(event.evidence_ids)} synthetic replay sources; "
                "confidence describes evidence coverage inside the demo, not real-world verification."
            ),
            evidence_ids=event.evidence_ids,
        )
