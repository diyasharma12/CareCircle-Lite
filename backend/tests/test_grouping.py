"""Unit tests for the pure overdue/due/done logic -- no DB involved."""

from datetime import datetime, timedelta
from types import SimpleNamespace

from app.grouping import group_tasks


def task(title, due_at, status="pending", completed_at=None):
    return SimpleNamespace(title=title, due_at=due_at, status=status, completed_at=completed_at)


def test_pending_task_past_due_is_overdue():
    now = datetime(2026, 1, 1, 12, 0)
    tasks = [task("BP tablet", now - timedelta(hours=1))]

    result = group_tasks(tasks, now)

    assert [t.title for t in result["overdue"]] == ["BP tablet"]
    assert result["due"] == []
    assert result["done"] == []


def test_pending_task_not_yet_due_is_due_not_overdue():
    now = datetime(2026, 1, 1, 12, 0)
    tasks = [task("Evening call", now + timedelta(hours=2))]

    result = group_tasks(tasks, now)

    assert result["overdue"] == []
    assert [t.title for t in result["due"]] == ["Evening call"]


def test_done_task_is_done_even_if_past_due_at():
    now = datetime(2026, 1, 1, 12, 0)
    tasks = [task("Morning tablet", now - timedelta(hours=5), status="done")]

    result = group_tasks(tasks, now)

    assert result["overdue"] == []
    assert result["due"] == []
    assert [t.title for t in result["done"]] == ["Morning tablet"]


def test_overdue_sorted_most_overdue_first():
    now = datetime(2026, 1, 1, 12, 0)
    tasks = [
        task("Due 1 hour ago", now - timedelta(hours=1)),
        task("Due 3 hours ago", now - timedelta(hours=3)),
    ]

    result = group_tasks(tasks, now)

    assert [t.title for t in result["overdue"]] == ["Due 3 hours ago", "Due 1 hour ago"]


def test_due_sorted_soonest_first():
    now = datetime(2026, 1, 1, 12, 0)
    tasks = [
        task("Due in 4 hours", now + timedelta(hours=4)),
        task("Due in 1 hour", now + timedelta(hours=1)),
    ]

    result = group_tasks(tasks, now)

    assert [t.title for t in result["due"]] == ["Due in 1 hour", "Due in 4 hours"]


def test_task_due_exactly_now_counts_as_overdue():
    now = datetime(2026, 1, 1, 12, 0)
    tasks = [task("Right now", now)]

    result = group_tasks(tasks, now)

    assert [t.title for t in result["overdue"]] == ["Right now"]
    assert result["due"] == []


def test_done_tasks_sorted_most_recently_completed_first():
    now = datetime(2026, 1, 1, 12, 0)
    tasks = [
        task("Older", now - timedelta(hours=5), status="done", completed_at=now - timedelta(hours=4)),
        task("Newer", now - timedelta(hours=5), status="done", completed_at=now - timedelta(hours=1)),
    ]

    result = group_tasks(tasks, now)

    assert [t.title for t in result["done"]] == ["Newer", "Older"]
