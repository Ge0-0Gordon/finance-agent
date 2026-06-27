from __future__ import annotations

from contextlib import nullcontext
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re
from typing import Any

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


def _clean_summary(value: str, max_length: int = 1200) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    return text[:max_length]


def _enabled_feeds(rss: dict) -> list[dict]:
    """Flatten legacy rss.feeds and grouped rss.groups.*.feeds."""
    feeds: list[dict] = []
    seen_ids: set[str] = set()

    def add(feed: dict, group: str) -> None:
        feed_id = str(feed.get("id", "")).strip()
        if not feed_id or feed_id in seen_ids or not feed.get("enabled", True):
            return
        feeds.append({**feed, "group": group})
        seen_ids.add(feed_id)

    for feed in rss.get("feeds", []):
        add(feed, "legacy")

    for group_name, group_config in rss.get("groups", {}).items():
        if not group_config.get("enabled", True):
            continue
        for feed in group_config.get("feeds", []):
            add(feed, group_name)

    return feeds


def collect_rss_documents(
    source_config: dict,
    request: ResearchRunRequest,
    client: Any | None = None,
) -> tuple[list[SourceDocument], list[str], dict]:
    rss = source_config.get("rss", {})
    if not rss.get("enabled", False):
        return [], ["RSS collection is disabled."], {
            "rss_source_total": 0,
            "rss_source_success": 0,
            "rss_source_failed": 0,
            "rss_group_coverage": {},
        }

    timeout = float(rss.get("timeout_seconds", 10))
    feeds = _enabled_feeds(rss)
    documents: list[SourceDocument] = []
    warnings: list[str] = []
    group_coverage: dict[str, dict[str, int]] = {}
    for feed in feeds:
        group = feed["group"]
        group_coverage.setdefault(
            group,
            {"configured": 0, "successful": 0, "failed": 0, "articles": 0},
        )
        group_coverage[group]["configured"] += 1

    successful_sources = 0
    failed_sources = 0
    managed_client = client is None
    active_client = client or httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={
            "User-Agent": "AI-Finance-Research-Agent/0.1 RSS Reader",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    context = active_client if managed_client else nullcontext(active_client)

    with context as rss_client:
        for feed in feeds:
            group = feed["group"]
            try:
                response = rss_client.get(feed["url"])
                response.raise_for_status()
                parsed = feedparser.parse(response.content)
                if parsed.bozo and not parsed.entries:
                    raise ValueError(f"invalid feed: {parsed.bozo_exception}")
                feed_documents: list[SourceDocument] = []
                for entry in parsed.entries:
                    published_at = _parse_date(
                        entry.get("published") or entry.get("updated"),
                        request.end_time,
                    )
                    if not request.start_time <= published_at <= request.end_time:
                        continue
                    url = str(
                        entry.get("link") or entry.get("guid") or entry.get("id") or ""
                    ).strip()
                    if not entry.get("title") or not url:
                        continue
                    feed_documents.append(
                        SourceDocument(
                            evidence_id="pending",
                            title=str(entry.get("title", "")).strip(),
                            summary=_clean_summary(str(entry.get("summary", ""))),
                            url=url,
                            source_name=feed.get("name", feed["id"]),
                            published_at=published_at,
                            source_type="rss",
                            metadata={"feed_id": feed["id"], "group": group},
                        )
                    )
                    if len(feed_documents) >= int(feed.get("max_items", 20)):
                        break
                for document in feed_documents:
                    document.evidence_id = f"S{len(documents) + 1:03d}"
                    documents.append(document)
                successful_sources += 1
                group_coverage[group]["successful"] += 1
                group_coverage[group]["articles"] += len(feed_documents)
            except Exception as exc:
                failed_sources += 1
                group_coverage[group]["failed"] += 1
                warnings.append(f"RSS source {feed.get('name', feed.get('id'))} failed: {exc}")

    return documents, warnings, {
        "rss_source_total": len(feeds),
        "rss_source_success": successful_sources,
        "rss_source_failed": failed_sources,
        "rss_group_coverage": group_coverage,
    }
