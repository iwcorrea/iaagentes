from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
router = APIRouter(prefix="/payments", tags=["payments"])
@router.get("/subscription")
def check_subscription(email: str = Depends(get_current_user)):
    # Mock subscription check
    return {"status": "active", "plan": "premium"}
@router.post("/subscribe")
def subscribe(email: str = Depends(get_current_user)):
    return {"message": "Subscription successful"}