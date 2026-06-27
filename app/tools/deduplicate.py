from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from rapidfuzz.fuzz import ratio

from app.models import SourceDocument


TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "ref",
    "source",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS
    ]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def normalize_title(title: str) -> str:
    return re.sub(r"\W+", " ", title.casefold()).strip()


def deduplicate_documents(
    documents: list[SourceDocument],
    title_threshold: int = 96,
) -> list[SourceDocument]:
    unique: list[SourceDocument] = []
    seen_urls: set[str] = set()
    normalized_titles: list[str] = []

    for document in documents:
        canonical_url = canonicalize_url(document.url)
        title = normalize_title(document.title)
        if canonical_url in seen_urls:
            continue
        if any(ratio(title, existing) >= title_threshold for existing in normalized_titles):
            continue
        document.url = canonical_url
        unique.append(document)
        seen_urls.add(canonical_url)
        normalized_titles.append(title)

    return unique


def validate_evidence_ids(
    evidence_ids: list[str],
    available_ids: set[str],
    *,
    context: str,
) -> None:
    invalid = sorted(set(evidence_ids) - available_ids)
    if invalid:
        raise ValueError(f"{context} references unknown evidence IDs: {invalid}")

