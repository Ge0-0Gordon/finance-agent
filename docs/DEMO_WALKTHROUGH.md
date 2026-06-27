# Demo Walkthrough

## 1. 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## 2. 配置本地 `.env`

复制示例文件：

```powershell
Copy-Item .env.example .env
```

阿里百炼 DeepSeek 必须使用百炼控制台提供的 **OpenAI-compatible endpoint**：

```env
LLM_MODEL=deepseek-v3
LLM_BASE_URL=https://<your-workspace-id>.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=<your-bailian-api-key>
LLM_TEMPERATURE=0
```

配置规则：

- 将占位符替换成百炼控制台实际显示的 workspace、模型 ID 和 API Key。
- `LLM_BASE_URL` 填写 OpenAI-compatible URL。
- 不要使用 `https://dashscope.aliyuncs.com/api/v1`。
- 不要使用普通 `apiHost`。
- 模型 ID 以控制台实际开通的名称为准，例如 `deepseek-v3`。
- `.env` 只能保存在本地，不得提交到 Git。
- 不要把 Key 放入截图、CSV、README、测试数据或命令历史。
- 如果 Key 已经出现在截图、CSV、README、GitHub 或提交历史中，立即到百炼控制台重置。

项目会忽略 `.env`、`*.csv` 和 `data/`。不要读取、复制或提交保存密钥的 CSV。

## 3. 运行模式

### Replay：离线稳定演示

```powershell
python -m app.cli run --topic "AI Agent 与金融科技" --since 7d --mode replay
```

使用 `demo/replay_ai_news.json` 和确定性分析，不需要网络或 API Key。建议先运行它确认本地环境和报告链路正常。

### Replay LLM：合成新闻 + 真实模型

```powershell
python -m app.cli run --topic "AI Agent 与金融科技" --since 7d --mode replay_llm
```

仍使用合成 Replay 新闻，但 EventExtractor 和 EventAnalysis 调用 OpenAI-compatible LLM。需要有效 `.env` 和网络。

### Live：RSS + 真实模型

```powershell
python -m app.cli run --topic "AI Agent 与金融科技" --since 7d --mode live
```

从 `config/sources.yaml` 获取 RSS，再调用 OpenAI-compatible LLM。需要有效 `.env`、API Key 和网络。

### Streamlit

```powershell
streamlit run app/ui/streamlit_app.py
```

在侧边栏选择 `replay`、`replay_llm` 或 `live`。演示现场优先从 `replay` 开始。

## 4. 查看输出

每次运行会创建：

```text
outputs/<run_id>/
  result.json
  report.md
  report.html
```

- `result.json`：来源、事件、结构化分析、证据 ID 和运行指标。
- `report.md`：可直接阅读或提交的 Markdown 报告。
- `report.html`：浏览器展示版报告。

PowerShell 查看最新运行：

```powershell
Get-ChildItem outputs -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

Replay 报告会明确标记为合成数据，不得把其中事件当作真实新闻。

