from datetime import datetime, timedelta, timezone

from app.config import PROJECT_ROOT, Settings
from app.llm_adapter import ReplayAnalysisAdapter
from app.models import Confidence, ResearchRunRequest, RunMode
from app.service import ResearchService


def test_replay_llm_uses_replay_sources_with_llm_adapter_boundary():
    settings = Settings(
        output_dir=PROJECT_ROOT / "outputs" / "test-runs",
        replay_file=PROJECT_ROOT / "demo" / "replay_ai_news.json",
        sources_file=PROJECT_ROOT / "config" / "sources.yaml",
    )
    factory_calls = []

    def fake_llm_factory(received_settings):
        factory_calls.append(received_settings)
        return ReplayAnalysisAdapter()

    now = datetime.now(timezone.utc)
    request = ResearchRunRequest(
        topic="AI finance",
        start_time=now - timedelta(days=7),
        end_time=now,
        mode=RunMode.REPLAY_LLM,
    )

    result = ResearchService(settings, llm_adapter_factory=fake_llm_factory).run(request)

    assert factory_calls == [settings]
    assert result.request.mode == RunMode.REPLAY_LLM
    assert all(source.source_type == "replay" for source in result.sources)
    assert all(analysis.confidence != Confidence.HIGH for analysis in result.analyses)
    assert [event.importance_score for event in result.events] == sorted(
        [event.importance_score for event in result.events],
        reverse=True,
    )
