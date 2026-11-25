import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.timeutils import utcnow


def _uuid() -> str:
    return str(uuid.uuid4())


class TaskCategory(str, enum.Enum):
    medicine = "medicine"
    appointment = "appointment"
    checkin = "checkin"
    other = "other"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    done = "done"


class CareRecipient(Base):
    __tablename__ = "care_recipients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow)

    tasks: Mapped[list["CareTask"]] = relationship(back_populates="recipient")


class FamilyMember(Base):
    __tablename__ = "family_members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    relation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow)


class CareTask(Base):
    __tablename__ = "care_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    recipient_id: Mapped[str] = mapped_column(ForeignKey("care_recipients.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[TaskCategory] = mapped_column(
        Enum(TaskCategory, native_enum=False), default=TaskCategory.other
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False), default=TaskStatus.pending, index=True
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("family_members.id"), nullable=True
    )
    completed_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("family_members.id"), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), default=utcnow, onupdate=utcnow
    )

    recipient: Mapped["CareRecipient"] = relationship(back_populates="tasks")
    created_by: Mapped["FamilyMember | None"] = relationship(foreign_keys=[created_by_id])
    completed_by: Mapped["FamilyMember | None"] = relationship(foreign_keys=[completed_by_id])


class AIInteraction(Base):
    """Every question asked of the assistant, logged for later review."""

    __tablename__ = "ai_interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    recipient_id: Mapped[str | None] = mapped_column(
        ForeignKey("care_recipients.id"), nullable=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of the task context sent
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow)
