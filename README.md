# AI Finance Research Agent

一个本地优先的 AI 金融研究 MVP：从 AI 新闻中提取重要事件，分析其技术意义、证券行业影响、量化投资影响、机会与风险，并生成带证据引用的 Markdown/HTML 报告。

## 架构

```text
Streamlit / CLI
→ ResearchService.run()
→ CollectAndDeduplicateNode
→ EventExtractorNode
→ EventAnalysisNode
→ ReportWriterNode
→ JSON / Markdown / HTML
```

Streamlit 与 CLI 共用同一服务和 workflow。FastAPI 不属于 MVP。

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

## LLM Configuration / 阿里百炼 DeepSeek 配置

项目统一通过 `ChatOpenAI` 的 OpenAI-compatible 接口调用模型：

```python
ChatOpenAI(
    model=settings.llm_model,
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
    temperature=settings.llm_temperature,
)
```

阿里百炼 DeepSeek 示例：

```env
LLM_MODEL=deepseek-v3
LLM_BASE_URL=https://<your-workspace-id>.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=<your-bailian-api-key>
LLM_TEMPERATURE=0
```

- `LLM_BASE_URL` 必须填写百炼控制台提供的 **OpenAI-compatible URL**。
- 不要填写 `https://dashscope.aliyuncs.com/api/v1`。
- 不要填写普通 `apiHost`。
- `LLM_MODEL` 以控制台实际开通的模型 ID 为准，例如 `deepseek-v3` 或控制台显示的具体模型名。
- `.env` 只用于本地，已被 `.gitignore` 排除，不得提交。
- 不要在 README、截图、CSV、测试或提交中保存真实 API Key。
- 如果 Key 曾出现在截图、CSV、README、GitHub 或提交历史中，应立即到百炼控制台重置。

## Replay、Replay LLM 与 Live

- `replay`：合成数据 + 确定性分析；完全离线、最稳定，不需要 API Key。
- `replay_llm`：固定合成数据 + 真实 LLM 事件抽取/分析；需要 API Key。
- `live`：真实 RSS + 真实 LLM 事件抽取/分析；需要 API Key 和网络。
- 报告默认输出简体中文，产品名、模型名和机构名等英文专有名词保持原文。

当前 live 是 **RSS-only**。RSS 按 `official_ai`、`research`、`china_ai`、`finance_tech` 分组配置，单个来源失败只会生成 warning，不会中止其余来源。

### 当前能力边界

- **P0/P0.6 已完成：** 四节点 workflow、三种运行模式、结构化分析、证据引用、中文 Markdown/HTML 报告、研究化量化措辞和报告限制说明。
- **P1.1 已完成：** 分组 RSS、旧配置兼容、来源失败隔离、来源/文章/事件覆盖统计。
- **P1.5 未实现：** Tavily/search collector。当前配置中的 `search.enabled: false` 只是未来扩展占位。
- 不包含 FastAPI、PDF、MCP、复杂 Dashboard 或数据库。

当前已配置并验证可解析的来源包括：

- OpenAI News、Google AI Blog、Google DeepMind Blog
- NVIDIA Blog、AWS Machine Learning Blog、Meta Engineering
- MIT News AI、Hugging Face Blog、Microsoft Research
- 量子位、36氪

### Future sources to add

以下来源尚未确认稳定公开 RSS，因此当前不写入不可用 URL：

- Anthropic Blog / News
- Meta AI Blog、Microsoft AI Blog
- 阿里云、通义、百炼官方新闻
- 机器之心
- 财联社科技 / AI
- 证券时报科技 / AI

### Tavily/search（P1.5，可选）

- 当前版本尚未实现 search collector。
- Tavily 可作为后续 RSS 补充，需要额外的 `TAVILY_API_KEY`。
- 真正启用 Tavily 必须实现搜索采集、时间过滤、来源标准化和失败处理；不能只把 `search.enabled` 改成 `true`。
- 未接入 search 时，live 的事件覆盖面受 RSS 来源限制。

## CLI

推荐按以下顺序验证：

```powershell
python -m app.cli run --topic "AI Agent 与金融科技" --since 7d --mode replay
python -m app.cli run --topic "AI Agent 与金融科技" --since 7d --mode replay_llm
python -m app.cli run --topic "AI Agent 与金融科技" --since 7d --mode live
streamlit run app/ui/streamlit_app.py
```

报告输出到 `outputs/<run_id>/`。

## Final Demo Path

```powershell
python -m app.cli run --topic "AI Agent 与金融科技" --since 7d --mode replay
python -m app.cli run --topic "AI Agent 与金融科技" --since 7d --mode replay_llm
python -m app.cli run --topic "AI Agent 与金融科技" --since 7d --mode live
streamlit run app/ui/streamlit_app.py
```

稳定示例产物：

- `outputs/sample_live/`
- `outputs/sample_replay_llm/`

## Known Limitations

- live 当前是 RSS-only。
- 来源偏官方博客、技术博客和研究机构。
- 尚未接入 Tavily/search。
- 当前来源不能代表全市场新闻覆盖。
- 报告仅用于研究辅助，不构成投资建议或交易决策依据。

## Streamlit

```powershell
streamlit run app/ui/streamlit_app.py
```

界面支持选择 `replay`、`replay_llm` 或 `live`，并展示四节点进度、中间分析和最终报告。

## Docker

```powershell
docker compose up --build
```

打开 `http://localhost:8501`。

完整演示步骤见 [docs/DEMO_WALKTHROUGH.md](docs/DEMO_WALKTHROUGH.md)。
