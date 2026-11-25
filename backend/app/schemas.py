from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, PlainSerializer

from app.models import TaskCategory, TaskStatus


def _to_naive_utc(v: datetime) -> datetime:
    """All datetimes are stored naive, in UTC. A client may send an offset
    (e.g. a trailing 'Z'); convert to UTC and drop the offset so it compares
    correctly against naive values like utcnow()."""
    if v.tzinfo is not None:
        return v.astimezone(timezone.utc).replace(tzinfo=None)
    return v


def _as_utc_iso(v: datetime) -> str:
    """Stamp the naive-UTC value with an explicit 'Z' offset on the way out,
    so clients (e.g. `new Date(iso)` in the browser) don't misread it as
    local time."""
    aware = v if v.tzinfo is not None else v.replace(tzinfo=timezone.utc)
    return aware.astimezone(timezone.utc).isoformat()


# Input: accept naive or offset datetimes, normalize to naive UTC for storage.
UtcIn = Annotated[datetime, AfterValidator(_to_naive_utc)]
# Output: always serialize with an explicit UTC offset.
UtcOut = Annotated[datetime, PlainSerializer(_as_utc_iso, return_type=str)]


class FamilyMemberBase(BaseModel):
    name: str
    relation: str | None = None


class FamilyMemberCreate(FamilyMemberBase):
    pass


class FamilyMemberOut(FamilyMemberBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


class CareRecipientBase(BaseModel):
    name: str
    notes: str | None = None


class CareRecipientCreate(CareRecipientBase):
    pass


class CareRecipientOut(CareRecipientBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


class CareTaskCreate(BaseModel):
    recipient_id: str
    title: str = Field(min_length=1, max_length=200)
    category: TaskCategory = TaskCategory.other
    due_at: UtcIn
    notes: str | None = None
    created_by_id: str | None = None


class CareTaskUpdate(BaseModel):
    title: str | None = None
    category: TaskCategory | None = None
    due_at: UtcIn | None = None
    notes: str | None = None


class CareTaskComplete(BaseModel):
    completed_by_id: str


class CareTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    recipient_id: str
    title: str
    category: TaskCategory
    due_at: UtcOut
    status: TaskStatus
    notes: str | None
    created_by: FamilyMemberOut | None
    completed_by: FamilyMemberOut | None
    completed_at: UtcOut | None
    created_at: UtcOut


class TodayResponse(BaseModel):
    overdue: list[CareTaskOut]
    due: list[CareTaskOut]
    done: list[CareTaskOut]
    as_of: UtcOut


class AskRequest(BaseModel):
    recipient_id: str
    question: str = Field(min_length=1, max_length=500)


class AIInteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    recipient_id: str | None
    question: str
    context: str
    answer: str
    latency_ms: int
    created_at: UtcOut
