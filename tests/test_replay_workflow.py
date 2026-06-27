from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import PROJECT_ROOT, Settings
from app.models import ResearchRunRequest, RunMode
from app.service import ResearchService


def test_replay_workflow_generates_complete_reports():
    settings = Settings(
        output_dir=PROJECT_ROOT / "outputs" / "test-runs",
        replay_file=PROJECT_ROOT / "demo" / "replay_ai_news.json",
        sources_file=PROJECT_ROOT / "config" / "sources.yaml",
    )
    end_time = datetime.now(timezone.utc)
    request = ResearchRunRequest(
        topic="AI finance",
        start_time=end_time - timedelta(days=7),
        end_time=end_time,
        max_events=8,
        mode=RunMode.REPLAY,
    )

    result = ResearchService(settings).run(request)

    assert result.metrics["collected_count"] == 15
    assert result.metrics["deduplicated_count"] == 14
    assert 5 <= len(result.events) <= 10
    assert len(result.events) == len(result.analyses)
    available = {source.evidence_id for source in result.sources}
    assert all(set(analysis.evidence_ids) <= available for analysis in result.analyses)
    assert Path(result.artifacts.result_json_path).exists()
    assert Path(result.artifacts.markdown_report_path).exists()
    assert Path(result.artifacts.html_report_path).exists()


def test_core_modules_do_not_import_entrypoint_frameworks():
    core_files = [
        PROJECT_ROOT / "app" / "service.py",
        PROJECT_ROOT / "app" / "workflow.py",
        *sorted((PROJECT_ROOT / "app" / "nodes").glob("*.py")),
    ]
    forbidden = ("import streamlit", "import typer", "import fastapi")
    for path in core_files:
        text = path.read_text(encoding="utf-8").lower()
        assert not any(item in text for item in forbidden), path
