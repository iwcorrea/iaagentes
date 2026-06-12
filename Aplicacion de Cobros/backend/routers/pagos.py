from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/pagos", tags=["pagos"])

@router.post("/", response_model=schemas.PaymentOut)
def make_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.id == payment.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db_payment = models.Payment(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.get("/", response_model=list[schemas.PaymentOut])
def list_payments(db: Session = Depends(get_db)):
    return db.query(models.Payment).all()