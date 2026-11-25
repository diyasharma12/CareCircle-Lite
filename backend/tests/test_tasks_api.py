from datetime import timedelta

from app.timeutils import utcnow


def _make_recipient(client):
    resp = client.post("/recipients", json={"name": "Amma"})
    assert resp.status_code == 201
    return resp.json()["id"]


def _make_member(client, name="Ravi"):
    resp = client.post("/family-members", json={"name": name, "relation": "Son"})
    assert resp.status_code == 201
    return resp.json()["id"]


def test_create_and_list_task(client):
    recipient_id = _make_recipient(client)
    due = (utcnow() + timedelta(hours=1)).isoformat()

    resp = client.post(
        "/tasks",
        json={"recipient_id": recipient_id, "title": "Evening BP tablet", "category": "medicine", "due_at": due},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Evening BP tablet"
    assert body["status"] == "pending"

    listed = client.get("/tasks", params={"recipient_id": recipient_id}).json()
    assert len(listed) == 1


def test_today_groups_overdue_due_and_done(client):
    recipient_id = _make_recipient(client)
    member_id = _make_member(client)
    now = utcnow()

    overdue_id = client.post(
        "/tasks",
        json={
            "recipient_id": recipient_id,
            "title": "Overdue tablet",
            "due_at": (now - timedelta(hours=1)).isoformat(),
        },
    ).json()["id"]

    client.post(
        "/tasks",
        json={
            "recipient_id": recipient_id,
            "title": "Upcoming call",
            "due_at": (now + timedelta(hours=2)).isoformat(),
        },
    )

    done_task = client.post(
        "/tasks",
        json={
            "recipient_id": recipient_id,
            "title": "Morning tablet",
            "due_at": (now - timedelta(hours=3)).isoformat(),
        },
    ).json()
    client.post(f"/tasks/{done_task['id']}/complete", json={"completed_by_id": member_id})

    today = client.get("/tasks/today", params={"recipient_id": recipient_id}).json()

    assert [t["id"] for t in today["overdue"]] == [overdue_id]
    assert len(today["due"]) == 1
    assert today["due"][0]["title"] == "Upcoming call"
    assert len(today["done"]) == 1
    assert today["done"][0]["title"] == "Morning tablet"
    assert today["done"][0]["completed_by"]["id"] == member_id


def test_complete_task_records_who_and_when(client):
    recipient_id = _make_recipient(client)
    member_id = _make_member(client, name="Priya")
    task_id = client.post(
        "/tasks",
        json={"recipient_id": recipient_id, "title": "BP tablet", "due_at": utcnow().isoformat()},
    ).json()["id"]

    resp = client.post(f"/tasks/{task_id}/complete", json={"completed_by_id": member_id})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "done"
    assert body["completed_by"]["name"] == "Priya"
    assert body["completed_at"] is not None


def test_completing_an_already_done_task_returns_409(client):
    """Two people tapping 'mark done' on the same task at once: the second
    request must not silently overwrite who completed it."""
    recipient_id = _make_recipient(client)
    ravi = _make_member(client, name="Ravi")
    priya = _make_member(client, name="Priya")
    task_id = client.post(
        "/tasks",
        json={"recipient_id": recipient_id, "title": "BP tablet", "due_at": utcnow().isoformat()},
    ).json()["id"]

    first = client.post(f"/tasks/{task_id}/complete", json={"completed_by_id": ravi})
    second = client.post(f"/tasks/{task_id}/complete", json={"completed_by_id": priya})

    assert first.status_code == 200
    assert second.status_code == 409
    # the task still shows Ravi as the one who completed it
    current = client.get("/tasks", params={"recipient_id": recipient_id}).json()[0]
    assert current["completed_by"]["name"] == "Ravi"
