# AI Finance Research Agent 一日 MVP 执行计划

## 目标

一天内交付可稳定演示的端到端 MVP：

```text
主题与时间范围
→ CollectAndDeduplicateNode
→ EventExtractorNode
→ EventAnalysisNode
→ ReportWriterNode
→ JSON / Markdown / HTML
```

Streamlit 和 CLI 只调用统一的 `ResearchService.run()`。核心工作流不依赖任何入口层。

## P0：必须完成

1. Pydantic 数据模型。
2. `ResearchService.run()`。
3. 四节点 LangGraph workflow。
4. Replay 数据加载、时间映射和去重。
5. EventExtractor、EventAnalysis 结构化输出。
6. evidence ID 完整性校验。
7. JSON、Markdown、HTML 报告。
8. CLI 与 Streamlit。
9. 最小测试。
10. Docker。

Replay 是默认演示模式，必须在没有网络和 API Key 时完整运行。Replay 使用明确标注的合成数据和确定性分析适配器；Live 模式使用 OpenAI-compatible LLM。

## P1：有时间再做

- Live RSS 完整验证。
- Tavily 搜索。
- 网页正文抓取。
- 更细的来源等级和置信度计算。
- UI 样式与下载体验。

## P2：不做

- FastAPI 实现、PDF、MCP、推送、用户系统。
- 定时任务、长期趋势数据库、向量数据库。
- 多轮 Supervisor、Bull/Bear 辩论。
- 自动交易、买卖评级、回测、本地 Ollama。

FastAPI 仅作为未来可调用 `ResearchService` 的扩展说明。

## 一日排期

| 时间 | 工作 | 验收 |
|---|---|---|
| 0–1h | 骨架、模型、配置 | 模型可验证，服务接口可调用 |
| 1–2.5h | Replay、RSS、去重 | 重复数据可合并，单源失败可见 |
| 2.5–4.5h | 事件抽取与分析 | 5–10 个事件，字段和证据完整 |
| 4.5–5.5h | 报告 | 生成 JSON/Markdown/HTML |
| 5.5–7h | CLI、Streamlit | 两入口共用服务层 |
| 7–8.5h | 测试、Docker | Replay 测试通过，容器可启动 |
| 8.5–10h | 缓冲 | 只修复 P0，不增加功能 |

## 验收标准

- Replay 可离线跑完整主链路。
- Streamlit 可输入主题、时间范围并展示四节点结果。
- CLI 可稳定运行并返回报告路径。
- 每个事件包含技术摘要、证券影响、量化影响、机会、风险、建议、置信度和 evidence IDs。
- 不输出买卖、目标价、仓位或收益承诺。
- 报告明确标注 Replay 数据和非投资建议。
- 最小测试通过，Docker 可启动。

