# P0 Checklist

## 规划与配置

- [x] 保存一日 MVP 计划
- [x] 创建 P0 checklist
- [x] 创建 README
- [x] 创建 `.env.example`
- [x] 创建最小来源配置
- [x] 创建含重复项的 Replay 数据

## 1. Pydantic 数据模型

- [x] `ResearchRunRequest`
- [x] `SourceDocument`
- [x] `EventRecord`
- [x] `EventAnalysis`
- [x] `ReportArtifacts`
- [x] `ResearchRunResult`
- [x] Workflow state

## 2. ResearchService

- [x] 实现 `ResearchService.run()`
- [x] 输入验证
- [x] 运行目录与 run ID
- [x] 节点进度回调
- [x] 错误和 warning 汇总

## 3. 四节点 Workflow

- [x] `CollectAndDeduplicateNode`
- [x] `EventExtractorNode`
- [x] `EventAnalysisNode`
- [x] `ReportWriterNode`
- [x] LangGraph 顺序连接

## 4. Replay 与去重

- [x] Replay JSON 加载
- [x] Replay 时间相对映射
- [x] URL 规范化
- [x] 标题标准化
- [x] 重复新闻合并
- [x] 显示去重前后数量

## 5. 结构化分析

- [x] OpenAI-compatible adapter
- [x] EventExtractor Pydantic 输出
- [x] EventAnalysis Pydantic 输出
- [x] Replay 确定性分析适配器
- [x] evidence ID 校验
- [x] 禁止交易指令

## 6. 报告

- [x] `result.json`
- [x] `report.md`
- [x] `report.html`
- [x] 来源索引
- [x] Replay 标识
- [x] 非投资建议声明

## 7. CLI

- [x] Replay 命令
- [x] Live 命令
- [x] 报告路径输出
- [x] 正确退出码

## 8. Streamlit

- [x] 主题输入
- [x] 时间范围
- [x] Replay/Live 选择
- [x] 四节点进度
- [x] 中间结果
- [x] 报告预览

## 9. 测试

- [x] 模型验证
- [x] Replay 加载
- [x] 去重
- [x] evidence ID 校验
- [x] Replay 端到端
- [x] 报告生成

## 10. Docker

- [x] Dockerfile
- [x] docker-compose.yml
- [x] 非 root 运行
- [x] 输出目录挂载
- [x] 本地 Streamlit 启动验证
- [ ] Docker 内 Streamlit 启动验证（当前机器未安装 Docker）

## P0.5

- [x] 阿里百炼 OpenAI-compatible 占位符配置
- [x] `.env`、`*.csv`、`data/` ignore
- [x] `replay_llm` 模式
- [x] Structured output → JSON fallback
- [x] Demo walkthrough
- [x] P0.5 最小测试
- [x] events 按 importance_score 降序
- [x] 默认中文报告
- [x] synthetic confidence 封顶 medium
- [x] 外部常识/待验证假设强制标注
- [x] 基于 EventAnalysis 的轻量总体摘要

## P0.6 / P1 RSS

- [x] 总体影响改为 3–5 条自然结论
- [x] 量化投资交易化措辞收紧
- [x] live 方法与限制声明 RSS-only
- [x] RSS 分组及旧格式兼容
- [x] 扩展已验证 RSS 来源
- [x] 来源覆盖统计
- [x] 单 RSS 失败隔离
- [x] Tavily 保留为 P1.5
