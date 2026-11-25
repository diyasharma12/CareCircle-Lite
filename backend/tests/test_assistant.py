from app.assistant import build_template_answer


def _context(overdue=None, due=None, done=None):
    return {
        "recipient": "Amma",
        "overdue": overdue or [],
        "due": due or [],
        "done": done or [],
    }


def test_mentions_pending_overdue_task_by_name():
    context = _context(overdue=[{"title": "Evening BP tablet", "due_at": "2026-01-01T20:00:00", "completed_by": None}])

    answer = build_template_answer("how is today going", context)

    assert "Amma" in answer
    assert "Evening BP tablet" in answer
    assert "still pending" in answer


def test_mentions_who_completed_a_done_task():
    context = _context(
        done=[
            {
                "title": "Morning BP tablet",
                "due_at": "2026-01-01T09:00:00",
                "completed_by": "Ravi",
                "completed_at": "2026-01-01T09:05:00",
            }
        ]
    )

    answer = build_template_answer("what's done", context)

    assert "Ravi" in answer
    assert "Morning BP tablet" in answer


def test_says_nothing_overdue_when_overdue_list_is_empty():
    context = _context(due=[{"title": "Evening call", "due_at": "2026-01-01T21:00:00", "completed_by": None}])

    answer = build_template_answer("any issues", context)

    assert "Nothing is overdue" in answer


def test_question_naming_a_person_highlights_their_completed_task():
    context = _context(
        done=[
            {"title": "9am tablet", "due_at": "2026-01-01T09:00:00", "completed_by": "Ravi", "completed_at": None},
            {"title": "8pm tablet", "due_at": "2026-01-01T20:00:00", "completed_by": "Priya", "completed_at": None},
        ]
    )

    answer = build_template_answer("did priya do her task", context)

    assert "Priya" in answer
    assert "8pm tablet" in answer
