from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import NotificationCreate, NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/", response_model=NotificationOut)
def create_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    # Por ahora, no guardamos en BD, solo devolvemos un dummy
    return {"id": 1, "user_id": notification.user_id, "message": notification.message, "created_at": "2025-01-01T00:00:00"}

@router.get("/", response_model=list[NotificationOut])
def list_notifications(db: Session = Depends(get_db)):
    return []