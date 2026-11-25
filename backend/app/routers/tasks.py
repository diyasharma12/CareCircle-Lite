from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.timeutils import utcnow

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=schemas.CareTaskOut, status_code=201)
def create_task(payload: schemas.CareTaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, payload)


@router.get("", response_model=list[schemas.CareTaskOut])
def list_tasks(recipient_id: str | None = None, db: Session = Depends(get_db)):
    return crud.list_tasks(db, recipient_id=recipient_id)


@router.get("/today", response_model=schemas.TodayResponse)
def today(recipient_id: str = Query(...), db: Session = Depends(get_db)):
    now = utcnow()
    grouping = crud.get_today_grouping(db, recipient_id, now=now)
    return schemas.TodayResponse(**grouping, as_of=now)


@router.patch("/{task_id}", response_model=schemas.CareTaskOut)
def update_task(task_id: str, payload: schemas.CareTaskUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_task(db, task_id, payload)
    except crud.TaskNotFound:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/complete", response_model=schemas.CareTaskOut)
def complete_task(task_id: str, payload: schemas.CareTaskComplete, db: Session = Depends(get_db)):
    try:
        return crud.complete_task(db, task_id, payload.completed_by_id)
    except crud.TaskNotFound:
        raise HTTPException(status_code=404, detail="Task not found")
    except crud.TaskAlreadyCompleted:
        raise HTTPException(
            status_code=409,
            detail="Task was already marked done by someone else a moment ago.",
        )
