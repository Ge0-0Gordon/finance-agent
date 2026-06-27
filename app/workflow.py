from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.config import Settings
from app.llm_adapter import AnalysisAdapter
from app.nodes import (
    CollectAndDeduplicateNode,
    EventAnalysisNode,
    EventExtractorNode,
    ReportWriterNode,
)
from app.workflow_state import WorkflowState


def build_workflow(settings: Settings, adapter: AnalysisAdapter, observer):
    builder = StateGraph(WorkflowState)
    builder.add_node("collect_and_deduplicate", CollectAndDeduplicateNode(settings, observer))
    builder.add_node("event_extractor", EventExtractorNode(adapter, observer))
    builder.add_node("event_analysis", EventAnalysisNode(adapter, observer))
    builder.add_node("report_writer", ReportWriterNode(settings, observer))

    builder.add_edge(START, "collect_and_deduplicate")
    builder.add_edge("collect_and_deduplicate", "event_extractor")
    builder.add_edge("event_extractor", "event_analysis")
    builder.add_edge("event_analysis", "report_writer")
    builder.add_edge("report_writer", END)
    return builder.compile()

