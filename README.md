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

- `replay`：合成数据 + 确定性分析；完全离线，不需要 API Key。
- `replay_llm`：合成数据 + 真实 LLM 事件抽取/分析；需要 API Key。
- `live`：RSS 数据 + 真实 LLM 事件抽取/分析；需要 API Key 和网络。
- 报告默认输出简体中文，产品名、模型名和机构名等英文专有名词保持原文。

## CLI

推荐按以下顺序验证：

```powershell
python -m app.cli run --topic "AI Agent 与金融科技" --since 7d --mode replay
python -m app.cli run --topic "AI Agent 与金融科技" --since 7d --mode replay_llm
python -m app.cli run --topic "AI Agent 与金融科技" --since 7d --mode live
streamlit run app/ui/streamlit_app.py
```

报告输出到 `outputs/<run_id>/`。

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
