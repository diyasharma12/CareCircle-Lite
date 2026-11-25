from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/family-members", tags=["family-members"])


@router.post("", response_model=schemas.FamilyMemberOut, status_code=201)
def create_family_member(payload: schemas.FamilyMemberCreate, db: Session = Depends(get_db)):
    return crud.create_family_member(db, payload)


@router.get("", response_model=list[schemas.FamilyMemberOut])
def list_family_members(db: Session = Depends(get_db)):
    return crud.list_family_members(db)
