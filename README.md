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

## Replay 与 Live

- `replay`：默认演示模式，使用明确标注的合成数据，不依赖网络或 LLM API。
- `live`：读取 `config/sources.yaml` 中的 RSS，并使用 OpenAI-compatible LLM；需要配置 `.env`。

## CLI

```powershell
python -m app.cli run --topic "AI Agent" --since 7d --mode replay
python -m app.cli run --topic "AI 芯片" --since 24h --mode live
```

报告输出到 `outputs/<run_id>/`。

## Streamlit

```powershell
streamlit run app/ui/streamlit_app.py
```

## Docker

```powershell
docker compose up --build
```

打开 `http://localhost:8501`。

