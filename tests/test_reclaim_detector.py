"""Tests for the reclaim tag detection service."""

from datetime import datetime, timezone

from src.domain.models.calendar_event import CalendarEvent
from src.services.calendar.reclaim_detector import ReclaimDetector


def _make_event(summary: str = "", description: str = "") -> CalendarEvent:
    return CalendarEvent(
        event_id="test-1",
        summary=summary,
        description=description,
        start=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        end=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
    )


def test_detects_reclaim_in_summary() -> None:
    detector = ReclaimDetector(reclaim_tag="[reclaim]")
    event = _make_event(summary="Focus time [reclaim]")
    assert detector.is_reclaim(event) is True


def test_detects_reclaim_in_description() -> None:
    detector = ReclaimDetector(reclaim_tag="[reclaim]")
    event = _make_event(description="auto-scheduled [reclaim] block")
    assert detector.is_reclaim(event) is True


def test_no_reclaim_tag() -> None:
    detector = ReclaimDetector(reclaim_tag="[reclaim]")
    event = _make_event(summary="Team standup")
    assert detector.is_reclaim(event) is False


def test_case_insensitive() -> None:
    detector = ReclaimDetector(reclaim_tag="[reclaim]")
    event = _make_event(summary="[RECLAIM] Deep Work")
    assert detector.is_reclaim(event) is True


def test_tag_events_sets_flag() -> None:
    detector = ReclaimDetector()
    events = [
        _make_event(summary="[reclaim] block"),
        _make_event(summary="Lunch"),
    ]
    tagged = detector.tag_events(events)
    assert tagged[0].is_reclaim is True
    assert tagged[1].is_reclaim is False
