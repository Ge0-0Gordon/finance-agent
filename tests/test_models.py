from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.models import ResearchRunRequest


def test_request_rejects_invalid_time_range():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        ResearchRunRequest(topic="AI", start_time=now, end_time=now - timedelta(hours=1))


def test_request_rejects_too_few_events():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        ResearchRunRequest(
            topic="AI",
            start_time=now - timedelta(days=1),
            end_time=now,
            max_events=4,
        )

