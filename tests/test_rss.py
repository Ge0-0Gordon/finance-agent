from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

from app.models import ResearchRunRequest, RunMode
from app.tools.rss import _enabled_feeds, collect_rss_documents


class _Response:
    def __init__(self, content: bytes, status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _Client:
    def __init__(self, responses: dict[str, _Response]) -> None:
        self.responses = responses

    def get(self, url: str) -> _Response:
        return self.responses[url]


def _rss_xml(published_at: datetime) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel><title>Test</title>
      <item>
        <title>AI research update</title>
        <link>https://example.com/ai-update</link>
        <description>&lt;p&gt;Evidence &lt;strong&gt;summary&lt;/strong&gt;&lt;/p&gt;</description>
        <pubDate>{format_datetime(published_at)}</pubDate>
      </item>
    </channel></rss>""".encode()


def test_enabled_feeds_supports_legacy_and_grouped_formats():
    rss = {
        "feeds": [{"id": "legacy", "url": "https://example.com/legacy"}],
        "groups": {
            "official_ai": {
                "enabled": True,
                "feeds": [{"id": "grouped", "url": "https://example.com/grouped"}],
            },
            "disabled": {
                "enabled": False,
                "feeds": [{"id": "ignored", "url": "https://example.com/ignored"}],
            },
        },
    }

    feeds = _enabled_feeds(rss)

    assert [(feed["id"], feed["group"]) for feed in feeds] == [
        ("legacy", "legacy"),
        ("grouped", "official_ai"),
    ]


def test_rss_failure_is_isolated_and_coverage_is_reported():
    now = datetime.now(timezone.utc)
    request = ResearchRunRequest(
        topic="AI",
        start_time=now - timedelta(days=1),
        end_time=now + timedelta(minutes=1),
        mode=RunMode.LIVE,
    )
    config = {
        "rss": {
            "enabled": True,
            "groups": {
                "official_ai": {
                    "enabled": True,
                    "feeds": [
                        {
                            "id": "working",
                            "name": "Working",
                            "url": "https://example.com/working.xml",
                        },
                        {
                            "id": "broken",
                            "name": "Broken",
                            "url": "https://example.com/broken.xml",
                        },
                    ],
                }
            },
        }
    }
    client = _Client(
        {
            "https://example.com/working.xml": _Response(_rss_xml(now)),
            "https://example.com/broken.xml": _Response(b"", status_code=500),
        }
    )

    documents, warnings, metrics = collect_rss_documents(config, request, client=client)

    assert len(documents) == 1
    assert documents[0].summary == "Evidence summary"
    assert len(warnings) == 1
    assert metrics["rss_source_total"] == 2
    assert metrics["rss_source_success"] == 1
    assert metrics["rss_source_failed"] == 1
    assert metrics["rss_group_coverage"]["official_ai"] == {
        "configured": 2,
        "successful": 1,
        "failed": 1,
        "articles": 1,
    }
