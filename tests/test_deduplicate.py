from datetime import datetime, timezone

import pytest

from app.models import SourceDocument
from app.tools.deduplicate import (
    canonicalize_url,
    deduplicate_documents,
    validate_evidence_ids,
)


def _document(evidence_id: str, title: str, url: str) -> SourceDocument:
    return SourceDocument(
        evidence_id=evidence_id,
        title=title,
        summary="summary",
        url=url,
        source_name="source",
        published_at=datetime.now(timezone.utc),
        source_type="test",
    )


def test_canonicalize_url_removes_tracking_parameters():
    assert (
        canonicalize_url("HTTPS://Example.com/news/?utm_source=test&id=1")
        == "https://example.com/news?id=1"
    )


def test_deduplicate_documents_by_canonical_url():
    documents = [
        _document("S001", "Agent launch", "https://example.com/a"),
        _document("S002", "Agent launch duplicate", "https://example.com/a?utm_source=x"),
    ]
    result = deduplicate_documents(documents)
    assert [item.evidence_id for item in result] == ["S001"]


def test_validate_evidence_ids_rejects_unknown_ids():
    with pytest.raises(ValueError, match="S999"):
        validate_evidence_ids(["S001", "S999"], {"S001"}, context="test")

