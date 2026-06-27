from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Protocol, TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

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
        output_language: str = "zh-CN",
    ) -> list[EventRecord]: ...

    def analyze_event(
        self,
        event: EventRecord,
        sources: list[SourceDocument],
        output_language: str = "zh-CN",
    ) -> EventAnalysis: ...


SchemaT = TypeVar("SchemaT", bound=BaseModel)


def _response_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return str(content)


def _parse_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```JSON").removeprefix("```")
        cleaned = cleaned.removesuffix("```").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Model response did not contain a JSON object")
    parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Model response JSON must be an object")
    return parsed


class OpenAICompatibleAdapter:
    def __init__(self, settings: Settings, model: Any | None = None) -> None:
        if model is None and not settings.llm_api_key:
            raise ValueError("LLM_API_KEY is required in replay_llm and live modes")
        self.model = model or ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            temperature=settings.llm_temperature,
        )
        prompt_dir = settings.project_root / "app" / "prompts"
        self.extract_prompt = (prompt_dir / "event_extractor.md").read_text(encoding="utf-8")
        self.analysis_prompt = (prompt_dir / "event_analysis.md").read_text(encoding="utf-8")

    def _invoke_validated(self, prompt: str, schema: type[SchemaT]) -> SchemaT:
        try:
            structured_result = self.model.with_structured_output(schema).invoke(prompt)
            return schema.model_validate(structured_result)
        except Exception as structured_error:
            fallback_prompt = (
                f"{prompt}\n\n"
                "The provider did not complete structured output. Return exactly one JSON "
                "object, with no Markdown fences or commentary, matching this JSON Schema:\n"
                f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
            )
            last_error: Exception = structured_error
            for _attempt in range(2):
                try:
                    response = self.model.invoke(fallback_prompt)
                    payload = _parse_json_object(_response_text(response.content))
                    return schema.model_validate(payload)
                except Exception as fallback_error:
                    last_error = fallback_error
            raise ValueError(
                f"{schema.__name__} validation failed after structured output and "
                "two JSON attempts"
            ) from last_error

    def extract_events(
        self,
        topic: str,
        sources: list[SourceDocument],
        max_events: int,
        output_language: str = "zh-CN",
    ) -> list[EventRecord]:
        payload = [item.model_dump(mode="json") for item in sources]
        prompt = self.extract_prompt.format(
            topic=topic,
            max_events=max_events,
            output_language=output_language,
            sources_json=json.dumps(payload, ensure_ascii=False),
        )
        result = self._invoke_validated(prompt, EventBatch)
        return result.events[:max_events]

    def analyze_event(
        self,
        event: EventRecord,
        sources: list[SourceDocument],
        output_language: str = "zh-CN",
    ) -> EventAnalysis:
        prompt = self.analysis_prompt.format(
            event_json=event.model_dump_json(),
            output_language=output_language,
            sources_json=json.dumps(
                [item.model_dump(mode="json") for item in sources],
                ensure_ascii=False,
            ),
        )
        return self._invoke_validated(prompt, EventAnalysis)


_REPLAY_EVENT_INFO = {
    "enterprise-agent": ("面向受监管行业的 governed AI Agent 平台", "product_launch", ["AtlasAI"], 92),
    "inference-chip": ("低成本 AI 推理加速器", "infrastructure", ["NovaChip"], 88),
    "financial-benchmark": ("面向金融 LLM 的开放评测基准", "research", ["FinBench"], 84),
    "ai-regulation": ("AI 投顾工具的模型风险记录要求", "regulation", ["Market regulator"], 95),
    "point-in-time-data": ("另类数据的 point-in-time 控制", "data_infrastructure", ["VectorLake"], 86),
    "agent-security": ("金融 Agent prompt injection 测试套件", "security", ["OpenShield"], 93),
    "broker-copilot": ("强调引用证据的证券研究 AI Copilot", "industry_adoption", ["BrokerLab"], 89),
}


_REPLAY_EVENT_SUMMARIES = {
    "enterprise-agent": "AtlasAI 发布合成演示用企业 Agent 平台，强调工具权限、审批门和可审计执行记录。",
    "inference-chip": "NovaChip 发布合成演示用 NC2 推理加速器，并有云服务商评估相关实例支持。",
    "financial-benchmark": "FinBench 发布合成演示用金融 LLM 评测，覆盖抽取、数值推理、引用准确性和拒答行为。",
    "ai-regulation": "合成监管咨询提出对 AI 辅助投顾记录模型变更、人工复核和事件处置流程。",
    "point-in-time-data": "VectorLake 增加时间戳血缘、修订历史和 point-in-time 导出，用于降低回测前视偏差。",
    "agent-security": "OpenShield 发布合成红队测试集，覆盖间接 prompt injection、不安全工具调用和敏感数据泄露。",
    "broker-copilot": "BrokerLab 开展合成内部试点，以引用覆盖率、修正率和节省时间衡量研究 Copilot。",
}


_REPLAY_ANALYSES = {
    "enterprise-agent": {
        "tech": "该产品组合工具权限、审批门和可审计执行，使企业 Agent 从开放式助手转向 governed workflow software。",
        "securities": "券商可在需要访问控制和审计证据的研究、运营场景中试用 governed Agent，但仍需承担集成与模型治理工作。",
        "quant": "受控工具调用可能提升研究编排效率，但生成结果仍需可复现性检查，并与生产交易执行隔离。",
        "opportunities": ["在低风险研究流程中试点强制审批门。"],
        "risks": ["工具权限可能配置错误，或被注入内容绕过。"],
        "recommendations": ["生产使用前验证审计完整性和权限隔离。"],
    },
    "inference-chip": {
        "tech": "该加速器面向 Transformer 推理降低能耗，可能扩展现有 GPU stack 之外的硬件选择。",
        "securities": "更低推理成本可能改善 AI 研究和客户服务的经济性，但取决于云端可用性与软件兼容性。",
        "quant": "更便宜的推理可支持更频繁的模型评估，但必须测量迁移成本和真实工作负载延迟。",
        "opportunities": ["在替代推理硬件上评测批量研究负载。"],
        "risks": ["供应商声明未必能转化为生产环境性价比。"],
        "recommendations": ["运行面向具体工作负载的成本、延迟和兼容性测试。"],
    },
    "financial-benchmark": {
        "tech": "该基准评测金融抽取、数值推理、引用准确性和合规敏感拒答行为。",
        "securities": "共享基准可用金融领域证据替代通用排行榜声明，从而改善模型采购与治理。",
        "quant": "可复现测试有助于比较研究助手，但 benchmark 表现不能证明存在可预测 alpha。",
        "opportunities": ["把该基准作为模型选型和回归测试的一道门槛。"],
        "risks": ["团队可能只优化 benchmark 任务而未改善真实流程。"],
        "recommendations": ["将公开分数与内部、按时间切分的评测集结合。"],
    },
    "ai-regulation": {
        "tech": "该提案关注文档、变更管理、人工复核和事件升级，而不是特定模型架构。",
        "securities": "证券机构的客户侧 AI 建议可能面临更高的治理和记录保存要求。",
        "quant": "内部量化研究可能通过模型清单、验证记录和变更控制间接受到影响。",
        "opportunities": ["建设可复用的 model card、审批记录和事件处置流程。"],
        "risks": ["合规要求可能延迟部署，或暴露未被记录的模型使用。"],
        "recommendations": ["将当前 AI 用例映射到提案中的文档与监督控制。"],
    },
    "point-in-time-data": {
        "tech": "时间戳血缘和数据集修订记录使历史时点的数据可用性更加明确。",
        "securities": "更好的数据血缘可增强研究可审计性和供应商治理。",
        "quant": "Point-in-time 导出直接针对 look-ahead bias，并提升回测可复现性。",
        "opportunities": ["为研究数据集加入可用时间戳和版本标识。"],
        "risks": ["错误的供应商时间戳可能制造回测有效性的假象。"],
        "recommendations": ["使用受控历史样本验证时间戳语义。"],
    },
    "agent-security": {
        "tech": "该套件测试 Agent workflow 中的间接 prompt injection、不安全工具调用和敏感数据泄露。",
        "securities": "金融机构在模型连接研究库或运营系统前，需要建立 Agent 专项控制。",
        "quant": "读取不可信文档的 Agent 可能污染研究或触发不安全工具，除非强制实施内容与执行边界。",
        "opportunities": ["将 prompt injection 测试加入模型和 Agent 发布门禁。"],
        "risks": ["被注入的来源文档可能操纵工具或泄露机密数据。"],
        "recommendations": ["隔离工具、限制凭证，并在 CI 中运行红队测试。"],
    },
    "broker-copilot": {
        "tech": "该试点把引用覆盖和分析师修正作为一等产品指标。",
        "securities": "Citation-first Copilot 可能减少研究草稿时间，同时保留复核责任。",
        "quant": "该流程可加速文献与新闻审阅，但不能替代数据验证或信号测试。",
        "opportunities": ["在有限试点中衡量引用覆盖率、修正率和节省时间。"],
        "risks": ["看似合理但支持力度不足的引用可能通过表面审核。"],
        "recommendations": ["要求来源级复核，并记录修正原因。"],
    },
}


class ReplayAnalysisAdapter:
    """Deterministic adapter for explicitly synthetic offline demonstrations."""

    def extract_events(
        self,
        topic: str,
        sources: list[SourceDocument],
        max_events: int,
        output_language: str = "zh-CN",
    ) -> list[EventRecord]:
        del topic, output_language
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
                    summary=_REPLAY_EVENT_SUMMARIES[key],
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
        output_language: str = "zh-CN",
    ) -> EventAnalysis:
        del output_language
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
                f"基于 {len(event.evidence_ids)} 条 synthetic Replay 来源；"
                "置信度只描述演示输入内部的证据覆盖，不代表现实真实性。"
            ),
            evidence_ids=event.evidence_ids,
        )
