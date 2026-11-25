from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/recipients", tags=["recipients"])


@router.post("", response_model=schemas.CareRecipientOut, status_code=201)
def create_recipient(payload: schemas.CareRecipientCreate, db: Session = Depends(get_db)):
    return crud.create_recipient(db, payload)


@router.get("", response_model=list[schemas.CareRecipientOut])
def list_recipients(db: Session = Depends(get_db)):
    return crud.list_recipients(db)
