from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import re

from app.llm_adapter import AnalysisAdapter
from app.models import Confidence, RunMode
from app.tools.deduplicate import validate_evidence_ids
from app.workflow_state import WorkflowState


EXTERNAL_FRAMEWORK_TERMS = ("SEC", "FINRA", "HIPAA", "MiFID", "GDPR")
PROHIBITED_ADVICE_PATTERNS = (
    re.compile(r"\b(?:BUY|SELL)\b", re.IGNORECASE),
    re.compile(r"买入|卖出|目标价|仓位|收益承诺"),
)
RESEARCH_LANGUAGE_REPLACEMENTS = (
    ("事件驱动型交易机会", "事件驱动研究观察方向"),
    ("事件驱动交易机会", "事件驱动研究观察方向"),
    ("交易机会", "研究观察方向"),
    ("可交易", "可作为后续验证假设"),
    ("可关注某类股票", "可将相关行业作为研究观察方向"),
)


def label_external_framework_usage(analysis, event, evidence):
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
        additions = [
            (
                f"外部常识/待验证假设：分析中涉及 {term}，但该框架未出现在输入 "
                "evidence 中；其适用性和具体要求需另行核验。"
            )
            for term in missing
        ]
        analysis = analysis.model_copy(
            update={
                "external_assumptions": [
                    *analysis.external_assumptions,
                    *additions,
                ]
            }
        )
    return analysis


def normalize_research_language(analysis):
    fields = [
        analysis.tech_product_summary,
        analysis.securities_impact,
        analysis.quant_impact,
        *analysis.opportunities,
        *analysis.risks,
        *analysis.recommendations,
    ]
    for pattern in PROHIBITED_ADVICE_PATTERNS:
        if any(pattern.search(value) for value in fields):
            raise ValueError(
                f"Analysis contains prohibited investment-advice language: {pattern.pattern}"
            )

    def rewrite(value: str) -> str:
        for old, new in RESEARCH_LANGUAGE_REPLACEMENTS:
            value = value.replace(old, new)
        return value

    quant_impact = rewrite(analysis.quant_impact)
    if "历史事件和市场数据验证" not in quant_impact:
        quant_impact = f"{quant_impact.rstrip()} 相关判断需用历史事件和市场数据验证。"
    return analysis.model_copy(
        update={
            "quant_impact": quant_impact,
            "opportunities": [rewrite(item) for item in analysis.opportunities],
            "recommendations": [rewrite(item) for item in analysis.recommendations],
        }
    )


def apply_confidence_policy(analysis, event, mode: RunMode):
    reasons: list[str] = []
    if mode in {RunMode.REPLAY, RunMode.REPLAY_LLM}:
        reasons.append(
            "使用 synthetic Replay 数据，confidence 只代表输入内部一致性，不代表现实真实性"
        )
    if len(event.evidence_ids) == 1:
        reasons.append(
            "该事件只有一个输入来源，证券和量化影响仍属于待验证推断"
        )
    if reasons and analysis.confidence == Confidence.HIGH:
        return analysis.model_copy(
            update={
                "confidence": Confidence.MEDIUM,
                "confidence_reason": (
                    f"{analysis.confidence_reason.rstrip()} "
                    f"置信度按规则封顶为 medium：{'；'.join(reasons)}。"
                ),
            }
        )
    return analysis


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
            analysis = label_external_framework_usage(analysis, event, evidence)
            analysis = normalize_research_language(analysis)
            analysis = apply_confidence_policy(
                analysis,
                event,
                state["request"].mode,
            )
            return analysis

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            analyses = list(executor.map(analyze, state["events"]))

        self.observer("analyze", {"status": "completed", "analysis_count": len(analyses)})
        return {"analyses": analyses}
