from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

from app.models import ResearchRunRequest, RunMode
from app.service import ResearchService


st.set_page_config(page_title="AI Finance Research Agent", layout="wide")
st.title("AI Finance Research Agent")
st.caption("Evidence-grounded one-day MVP · Streamlit and CLI share one workflow")

with st.sidebar:
    topic = st.text_input("研究主题", value="AI Agent 与金融科技")
    period = st.selectbox("时间范围", ["最近 24 小时", "最近 7 天", "自定义天数"])
    custom_days = (
        st.number_input("回溯天数", min_value=1, max_value=30, value=3)
        if period == "自定义天数"
        else None
    )
    mode_value = st.radio("数据模式", ["replay", "live"], horizontal=True)
    max_events = st.slider("最大事件数", min_value=5, max_value=10, value=8)
    submitted = st.button("运行分析", type="primary", use_container_width=True)

if submitted:
    if period == "最近 24 小时":
        lookback = timedelta(hours=24)
    elif period == "最近 7 天":
        lookback = timedelta(days=7)
    else:
        lookback = timedelta(days=int(custom_days))

    end_time = datetime.now(timezone.utc)
    request = ResearchRunRequest(
        topic=topic,
        start_time=end_time - lookback,
        end_time=end_time,
        max_events=max_events,
        mode=RunMode(mode_value),
    )

    status = st.status("准备运行四节点 workflow…", expanded=True)
    stage_labels = {
        "collect": "1/4 采集与去重",
        "extract": "2/4 事件抽取",
        "analyze": "3/4 综合分析",
        "report": "4/4 报告生成",
    }

    def observer(stage: str, payload: dict) -> None:
        label = stage_labels.get(stage, stage)
        state = payload.get("status", "")
        status.write(f"{label}: {state}")

    try:
        result = ResearchService().run(request, observer=observer)
        status.update(label="运行完成", state="complete", expanded=False)
    except Exception as exc:
        status.update(label="运行失败", state="error", expanded=True)
        st.error(str(exc))
        st.stop()

    if result.request.mode == RunMode.REPLAY:
        st.warning("当前结果使用合成 Replay Demo Data，不代表真实或当前新闻。")

    col1, col2, col3 = st.columns(3)
    col1.metric("采集条数", result.metrics.get("collected_count", 0))
    col2.metric("去重后", result.metrics.get("deduplicated_count", 0))
    col3.metric("重点事件", len(result.events))

    st.subheader("重点事件与中间分析")
    analysis_by_event = {item.event_id: item for item in result.analyses}
    for event in result.events:
        analysis = analysis_by_event[event.event_id]
        with st.expander(
            f"{event.title} · 重要性 {event.importance_score:.0f} · {analysis.confidence.value}"
        ):
            st.markdown(f"**事件摘要：** {event.summary}")
            st.markdown(f"**技术/产品：** {analysis.tech_product_summary}")
            st.markdown(f"**证券行业：** {analysis.securities_impact}")
            st.markdown(f"**量化投资：** {analysis.quant_impact}")
            st.markdown("**机会：**\n" + "\n".join(f"- {x}" for x in analysis.opportunities))
            st.markdown("**风险：**\n" + "\n".join(f"- {x}" for x in analysis.risks))
            st.markdown("**建议：**\n" + "\n".join(f"- {x}" for x in analysis.recommendations))
            st.caption("Evidence: " + ", ".join(analysis.evidence_ids))

    st.subheader("最终报告")
    markdown_report = Path(result.artifacts.markdown_report_path).read_text(encoding="utf-8")
    st.markdown(markdown_report)
    st.caption(f"HTML: {result.artifacts.html_report_path}")
    st.caption(f"JSON: {result.artifacts.result_json_path}")

