from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/clientes", tags=["clientes"])

@router.get("/", response_model=list[schemas.ClientOut])
def list_clients(db: Session = Depends(get_db)):
    return db.query(models.Client).all()

@router.post("/", response_model=schemas.ClientOut)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    db_client = models.Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client