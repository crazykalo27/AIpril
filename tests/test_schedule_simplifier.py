"""Tests for the schedule simplification service."""

from datetime import datetime, timezone

from src.domain.models.calendar_event import CalendarEvent
from src.services.calendar.schedule_simplifier import ScheduleSimplifier


def _dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 1, 1, hour, minute, tzinfo=timezone.utc)


def test_empty_events_produces_single_free_block() -> None:
    simplifier = ScheduleSimplifier()
    blocks = simplifier.simplify([], _dt(9), _dt(17))
    assert len(blocks) == 1
    assert blocks[0].ask_user is True
    assert blocks[0].label == "free"


def test_single_event_produces_three_blocks() -> None:
    simplifier = ScheduleSimplifier()
    event = CalendarEvent(
        event_id="e1",
        summary="Meeting",
        start=_dt(10),
        end=_dt(11),
        is_reclaim=False,
    )
    blocks = simplifier.simplify([event], _dt(9), _dt(12))
    assert len(blocks) == 3
    assert blocks[0].ask_user is True   # 9-10 free
    assert blocks[1].ask_user is False  # 10-11 busy
    assert blocks[2].ask_user is True   # 11-12 free


def test_reclaim_event_labeled() -> None:
    simplifier = ScheduleSimplifier()
    event = CalendarEvent(
        event_id="e2",
        summary="Focus",
        start=_dt(9),
        end=_dt(10),
        is_reclaim=True,
    )
    blocks = simplifier.simplify([event], _dt(9), _dt(11))
    assert blocks[0].label == "reclaim"
