from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db
router = APIRouter(prefix="/payments", tags=["payments"])
@router.post("/", response_model=schemas.PaymentOut)
def create_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db), current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "maestro":
        raise HTTPException(status_code=403, detail="Only maestros can record payments")
    db_payment = models.Payment(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment
@router.get("/", response_model=List[schemas.PaymentOut])
def get_all_payments(db: Session = Depends(get_db), current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "maestro":
        raise HTTPException(status_code=403, detail="Access forbidden")
    return db.query(models.Payment).all()
@router.get("/my-payments", response_model=List[schemas.PaymentOut])
def get_my_payments(db: Session = Depends(get_db), current_user: dict = Depends(auth.get_current_user)):
    return db.query(models.Payment).filter(models.Payment.user_id == current_user["id"]).all()