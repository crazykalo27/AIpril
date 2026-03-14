"""Tests for the prompt state decision use case."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.domain.enums.prompt_state import PromptState
from src.domain.models.calendar_event import CalendarEvent
from src.application.use_cases.determine_prompt_state import DeterminePromptState


def test_should_prompt_when_no_events() -> None:
    calendar_client = MagicMock()
    calendar_client.list_events.return_value = []

    reclaim_detector = MagicMock()

    use_case = DeterminePromptState(
        calendar_client=calendar_client,
        reclaim_detector=reclaim_detector,
    )

    result = use_case.execute()
    assert result == PromptState.SHOULD_PROMPT


def test_suppressed_when_reclaim_event_present() -> None:
    event = CalendarEvent(
        event_id="r1",
        summary="Focus",
        start=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        end=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        is_reclaim=True,
    )
    calendar_client = MagicMock()
    calendar_client.list_events.return_value = [event]

    reclaim_detector = MagicMock()
    reclaim_detector.tag_events.return_value = [event]

    use_case = DeterminePromptState(
        calendar_client=calendar_client,
        reclaim_detector=reclaim_detector,
    )

    result = use_case.execute()
    assert result == PromptState.SUPPRESSED_RECLAIM


def test_suppressed_when_non_reclaim_event_present() -> None:
    event = CalendarEvent(
        event_id="m1",
        summary="Standup",
        start=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        end=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        is_reclaim=False,
    )
    calendar_client = MagicMock()
    calendar_client.list_events.return_value = [event]

    reclaim_detector = MagicMock()
    reclaim_detector.tag_events.return_value = [event]

    use_case = DeterminePromptState(
        calendar_client=calendar_client,
        reclaim_detector=reclaim_detector,
    )

    result = use_case.execute()
    assert result == PromptState.SUPPRESSED_EVENT
