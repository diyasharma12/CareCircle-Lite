"""Pure logic for sorting tasks into overdue / due / done.

Kept separate from the DB layer so it can be unit tested with plain
objects and no database at all.
"""

from datetime import datetime
from typing import Protocol


class TaskLike(Protocol):
    due_at: datetime
    status: object  # TaskStatus, compared by .value where needed


def is_done(task: TaskLike) -> bool:
    status = task.status
    value = getattr(status, "value", status)
    return value == "done"


def group_tasks(tasks: list, now: datetime) -> dict[str, list]:
    """Split tasks into overdue, due (pending, not yet due) and done.

    A pending task is overdue once its due_at has passed `now`; otherwise
    it is simply due. Overdue tasks are sorted most-overdue first (oldest
    due_at first). Due tasks are sorted soonest first. Done tasks are
    sorted most-recently-completed first.
    """
    overdue, due, done = [], [], []
    for task in tasks:
        if is_done(task):
            done.append(task)
        elif task.due_at <= now:
            overdue.append(task)
        else:
            due.append(task)

    overdue.sort(key=lambda t: t.due_at)
    due.sort(key=lambda t: t.due_at)
    done.sort(key=lambda t: t.completed_at or t.due_at, reverse=True)

    return {"overdue": overdue, "due": due, "done": done}
