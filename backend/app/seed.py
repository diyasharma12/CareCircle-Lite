"""Seeds a bit of demo data on first startup, so the app is usable the
moment `docker compose up` finishes instead of showing an empty screen.
Runs only when the recipients table is empty, so it never duplicates data
or clobbers anything a real session has created.
"""

from datetime import timedelta

from sqlalchemy.orm import Session

from app import models
from app.timeutils import utcnow


def seed_demo_data(db: Session) -> None:
    if db.query(models.CareRecipient).count() > 0:
        return

    recipient = models.CareRecipient(name="Amma", notes="Lives with Ravi, visited weekly by Priya")
    ravi = models.FamilyMember(name="Ravi", relation="Son")
    priya = models.FamilyMember(name="Priya", relation="Daughter")
    db.add_all([recipient, ravi, priya])
    db.flush()

    now = utcnow()
    tasks = [
        models.CareTask(
            recipient_id=recipient.id,
            title="Morning BP tablet",
            category=models.TaskCategory.medicine,
            due_at=now - timedelta(hours=3),
            status=models.TaskStatus.done,
            completed_by_id=ravi.id,
            completed_at=now - timedelta(hours=2, minutes=50),
            created_by_id=ravi.id,
        ),
        models.CareTask(
            recipient_id=recipient.id,
            title="Evening BP tablet",
            category=models.TaskCategory.medicine,
            due_at=now - timedelta(hours=1),
            created_by_id=priya.id,
        ),
        models.CareTask(
            recipient_id=recipient.id,
            title="Cardiologist appointment call",
            category=models.TaskCategory.appointment,
            due_at=now + timedelta(hours=2),
            notes="Confirm Tuesday 4pm slot",
            created_by_id=priya.id,
        ),
        models.CareTask(
            recipient_id=recipient.id,
            title="Evening check-in call",
            category=models.TaskCategory.checkin,
            due_at=now + timedelta(hours=4),
            created_by_id=ravi.id,
        ),
    ]
    db.add_all(tasks)
    db.commit()
