from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from app.models import ResearchRunRequest, SourceDocument


def _parse_date(value: str | None, fallback: datetime) -> datetime:
    if not value:
        return fallback
    try:
        parsed = parsedate_to_datetime(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return fallback


def collect_rss_documents(
    source_config: dict,
    request: ResearchRunRequest,
) -> tuple[list[SourceDocument], list[str]]:
    rss = source_config.get("rss", {})
    if not rss.get("enabled", False):
        return [], ["RSS collection is disabled."]

    timeout = float(rss.get("timeout_seconds", 10))
    documents: list[SourceDocument] = []
    warnings: list[str] = []

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        for feed in rss.get("feeds", []):
            if not feed.get("enabled", True):
                continue
            try:
                response = client.get(feed["url"])
                response.raise_for_status()
                parsed = feedparser.parse(response.content)
                for entry in parsed.entries:
                    published_at = _parse_date(
                        entry.get("published") or entry.get("updated"),
                        request.end_time,
                    )
                    if not request.start_time <= published_at <= request.end_time:
                        continue
                    documents.append(
                        SourceDocument(
                            evidence_id=f"S{len(documents) + 1:03d}",
                            title=str(entry.get("title", "")).strip(),
                            summary=str(entry.get("summary", "")).strip(),
                            url=str(entry.get("link", "")).strip(),
                            source_name=feed.get("name", feed["id"]),
                            published_at=published_at,
                            source_type="rss",
                            metadata={"feed_id": feed["id"]},
                        )
                    )
            except Exception as exc:
                warnings.append(f"RSS source {feed.get('name', feed.get('id'))} failed: {exc}")

    return [item for item in documents if item.title and item.url], warnings

