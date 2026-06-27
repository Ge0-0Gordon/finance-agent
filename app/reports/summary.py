from __future__ import annotations

import re

from app.models import EventAnalysis, EventRecord, ReportSummary


THEMES = (
    ("合规 Agent 生产化", ("合规", "监管", "audit", "governance")),
    ("模型能力与基础设施升级", ("模型", "gpt", "claude", "gemini", "推理", "算力")),
    ("AI 安全与可信工具化", ("安全", "security", "prompt injection", "红队", "风险")),
    ("金融数据与评测治理", ("数据", "benchmark", "评测", "引用", "血缘")),
    ("量化研究流程自动化", ("agent", "自动化", "研究流程", "computer use", "回测")),
)


def _first_sentence(text: str) -> str:
    normalized = text.strip()
    match = re.search(r"[。！？]|(?<!\d)[.!?](?=\s|$)", normalized)
    return normalized[: match.end()] if match else normalized


def _impact_conclusions(
    events: list[EventRecord],
    analyses: list[EventAnalysis],
    field: str,
) -> list[str]:
    conclusions: list[str] = []
    used_impacts: set[str] = set()
    entries = []
    for event, analysis in zip(events, analyses, strict=True):
        corpus = " ".join(
            [
                event.title,
                event.summary,
                analysis.tech_product_summary,
                analysis.securities_impact,
                analysis.quant_impact,
                *analysis.opportunities,
                *analysis.risks,
                *analysis.recommendations,
            ]
        ).casefold()
        entries.append((event, analysis, corpus))

    for theme, keywords in THEMES:
        matching = [
            (event, analysis)
            for event, analysis, corpus in entries
            if any(keyword.casefold() in corpus for keyword in keywords)
        ]
        impacts = []
        for _event, analysis in matching:
            impact = _first_sentence(getattr(analysis, field))
            if impact and impact not in used_impacts:
                impacts.append(impact)
                used_impacts.add(impact)
            if len(impacts) == 2:
                break
        if not impacts:
            continue
        conclusion = f"{theme}：{impacts[0]}"
        if len(impacts) == 2:
            conclusion += f" 同一主题下的另一条已有分析指出：{impacts[1]}"
        conclusions.append(conclusion)
        if len(conclusions) == 5:
            break

    if len(conclusions) < 4:
        for event, analysis, _corpus in entries:
            impact = _first_sentence(getattr(analysis, field))
            if not impact or impact in used_impacts:
                continue
            conclusions.append(f"其他重点影响（{event.title}）：{impact}")
            used_impacts.add(impact)
            if len(conclusions) == 4:
                break
    return conclusions


def _unique(items: list[str], limit: int) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = item.strip()
        if normalized and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
        if len(result) >= limit:
            break
    return result


def build_report_summary(
    events: list[EventRecord],
    analyses: list[EventAnalysis],
) -> ReportSummary:
    """Build a deterministic synthesis using only existing event analyses."""
    if not events:
        raise ValueError("Cannot build report summary without events")
    analysis_by_event = {item.event_id: item for item in analyses}
    ordered_analyses = [analysis_by_event[event.event_id] for event in events]
    leading_titles = "、".join(event.title for event in events[:3])
    executive_summary = (
        f"本次共识别 {len(events)} 个重点事件。按 importance_score 排名靠前的事件为"
        f"{leading_titles}。以下总体判断仅压缩已有 EventAnalysis，不引入额外事实。"
    )
    securities_overview = _impact_conclusions(
        events,
        ordered_analyses,
        "securities_impact",
    )
    quant_overview = _impact_conclusions(
        events,
        ordered_analyses,
        "quant_impact",
    )
    return ReportSummary(
        executive_summary=executive_summary,
        securities_overview=securities_overview,
        quant_overview=quant_overview,
        top_opportunities=_unique(
            [value for item in ordered_analyses for value in item.opportunities],
            5,
        ),
        top_risks=_unique(
            [value for item in ordered_analyses for value in item.risks],
            5,
        ),
        priority_recommendations=_unique(
            [value for item in ordered_analyses for value in item.recommendations],
            5,
        ),
    )
