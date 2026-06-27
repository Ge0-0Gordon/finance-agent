from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from app.models import ResearchRunRequest, SourceDocument


def load_replay_documents(
    path: Path,
    request: ResearchRunRequest,
) -> tuple[list[SourceDocument], list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    metadata = payload.get("metadata", {})
    if not metadata.get("synthetic"):
        raise ValueError("Replay dataset must be explicitly marked as synthetic")

    window_seconds = max((request.end_time - request.start_time).total_seconds(), 1)
    documents: list[SourceDocument] = []
    for index, item in enumerate(payload.get("items", []), start=1):
        offset = timedelta(hours=float(item.get("published_offset_hours", index)))
        published_at = request.end_time - offset
        if published_at < request.start_time:
            wrapped_seconds = offset.total_seconds() % window_seconds
            published_at = request.end_time - timedelta(seconds=wrapped_seconds)
        documents.append(
            SourceDocument(
                evidence_id=f"S{index:03d}",
                title=item["title"],
                summary=item["summary"],
                url=item["url"],
                source_name=item["source_name"],
                published_at=published_at,
                source_type="replay",
                metadata={"event_key": item["event_key"], "synthetic": True},
            )
        )

    return documents, ["Replay mode uses synthetic demonstration data."]

