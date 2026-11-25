from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import models, schemas
from app.grouping import group_tasks
from app.timeutils import utcnow


class TaskAlreadyCompleted(Exception):
    """Raised when two people try to complete the same task at once."""


class TaskNotFound(Exception):
    pass


def create_recipient(db: Session, payload: schemas.CareRecipientCreate) -> models.CareRecipient:
    recipient = models.CareRecipient(**payload.model_dump())
    db.add(recipient)
    db.commit()
    db.refresh(recipient)
    return recipient


def list_recipients(db: Session) -> list[models.CareRecipient]:
    return list(db.scalars(select(models.CareRecipient)))


def create_family_member(db: Session, payload: schemas.FamilyMemberCreate) -> models.FamilyMember:
    member = models.FamilyMember(**payload.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def list_family_members(db: Session) -> list[models.FamilyMember]:
    return list(db.scalars(select(models.FamilyMember)))


def create_task(db: Session, payload: schemas.CareTaskCreate) -> models.CareTask:
    task = models.CareTask(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks(db: Session, recipient_id: str | None = None) -> list[models.CareTask]:
    stmt = select(models.CareTask)
    if recipient_id:
        stmt = stmt.where(models.CareTask.recipient_id == recipient_id)
    return list(db.scalars(stmt))


def get_task(db: Session, task_id: str) -> models.CareTask | None:
    return db.get(models.CareTask, task_id)


def update_task(db: Session, task_id: str, payload: schemas.CareTaskUpdate) -> models.CareTask:
    task = get_task(db, task_id)
    if task is None:
        raise TaskNotFound(task_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def complete_task(db: Session, task_id: str, completed_by_id: str) -> models.CareTask:
    """Mark a task done, safe against two people tapping 'done' at once.

    The UPDATE is conditioned on the row still being pending. Only one of
    two concurrent requests will match a row and apply; the other affects
    zero rows and is told the task was already completed, instead of
    silently overwriting who-did-it-and-when.
    """
    now = utcnow()
    result = db.execute(
        update(models.CareTask)
        .where(models.CareTask.id == task_id, models.CareTask.status == models.TaskStatus.pending)
        .values(status=models.TaskStatus.done, completed_by_id=completed_by_id, completed_at=now)
    )
    db.commit()

    if result.rowcount == 0:
        task = get_task(db, task_id)
        if task is None:
            raise TaskNotFound(task_id)
        raise TaskAlreadyCompleted(task_id)

    task = get_task(db, task_id)
    db.refresh(task)
    return task


def get_today_grouping(db: Session, recipient_id: str, now: datetime | None = None) -> dict:
    now = now or utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    stmt = select(models.CareTask).where(
        models.CareTask.recipient_id == recipient_id,
        models.CareTask.due_at >= start_of_day,
        models.CareTask.due_at < end_of_day,
    )
    tasks = list(db.scalars(stmt))
    return group_tasks(tasks, now)


def log_ai_interaction(
    db: Session,
    recipient_id: str | None,
    question: str,
    context: str,
    answer: str,
    latency_ms: int,
) -> models.AIInteraction:
    interaction = models.AIInteraction(
        recipient_id=recipient_id,
        question=question,
        context=context,
        answer=answer,
        latency_ms=latency_ms,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction
