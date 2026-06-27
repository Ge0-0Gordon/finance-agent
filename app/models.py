from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RunMode(str, Enum):
    REPLAY = "replay"
    REPLAY_LLM = "replay_llm"
    LIVE = "live"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ResearchRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str = Field(min_length=2, max_length=200)
    start_time: datetime
    end_time: datetime
    max_events: int = Field(default=8, ge=5, le=10)
    mode: RunMode = RunMode.REPLAY
    output_language: str = Field(default="zh-CN", min_length=2, max_length=20)
    output_formats: list[str] = Field(default_factory=lambda: ["markdown", "html"])

    @field_validator("output_formats")
    @classmethod
    def validate_output_formats(cls, value: list[str]) -> list[str]:
        formats = list(dict.fromkeys(item.lower() for item in value))
        invalid = set(formats) - {"markdown", "html"}
        if invalid:
            raise ValueError(f"Unsupported output formats: {sorted(invalid)}")
        return formats

    @model_validator(mode="after")
    def validate_time_range(self) -> "ResearchRunRequest":
        if self.start_time.tzinfo is None or self.end_time.tzinfo is None:
            raise ValueError("start_time and end_time must include timezone information")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be later than start_time")
        return self


class SourceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    title: str
    summary: str
    url: str
    source_name: str
    published_at: datetime
    source_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    title: str
    event_type: str
    summary: str
    entities: list[str] = Field(default_factory=list)
    importance_score: float = Field(ge=0, le=100)
    evidence_ids: list[str] = Field(min_length=1)


class EventBatch(BaseModel):
    events: list[EventRecord]


class EventAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    tech_product_summary: str
    securities_impact: str
    quant_impact: str
    opportunities: list[str]
    risks: list[str]
    recommendations: list[str]
    external_assumptions: list[str] = Field(default_factory=list)
    confidence: Confidence
    confidence_reason: str
    evidence_ids: list[str] = Field(min_length=1)

    @field_validator("external_assumptions")
    @classmethod
    def validate_external_assumption_labels(cls, value: list[str]) -> list[str]:
        prefix = "外部常识/待验证假设："
        invalid = [item for item in value if not item.startswith(prefix)]
        if invalid:
            raise ValueError(f"external_assumptions must start with '{prefix}'")
        return value


class ReportSummary(BaseModel):
    executive_summary: str
    securities_overview: str
    quant_overview: str
    top_opportunities: list[str] = Field(default_factory=list)
    top_risks: list[str] = Field(default_factory=list)
    priority_recommendations: list[str] = Field(default_factory=list)


class ReportArtifacts(BaseModel):
    result_json_path: str
    markdown_report_path: str
    html_report_path: str


class ResearchRunResult(BaseModel):
    run_id: str
    request: ResearchRunRequest
    sources: list[SourceDocument]
    events: list[EventRecord]
    analyses: list[EventAnalysis]
    artifacts: ReportArtifacts
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, int] = Field(default_factory=dict)
