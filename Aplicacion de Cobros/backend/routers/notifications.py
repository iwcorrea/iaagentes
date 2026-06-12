from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import TokenRegister, NotificationRequest
from ..auth import get_current_user
import requests
import os
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
@router.post("/register")
def register_token(reg: TokenRegister, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    if reg.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to register token for this user")
    user = db.query(User).filter(User.id == reg.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.push_token = reg.token
    db.commit()
    return {"status": "token_registered"}
@router.post("/send")
def send_notification(req: NotificationRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_expo_push, req.token, req.title, req.body, req.data)
    return {"status": "scheduled"}
def send_expo_push(token: str, title: str, body: str, data: dict):
    payload = {
        "to": token,
        "sound": "default",
        "title": title,
        "body": body,
        "data": data,
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    token_auth = os.getenv("EXPO_ACCESS_TOKEN")
    if token_auth:
        headers["Authorization"] = f"Bearer {token_auth}"
    try:
        response = requests.post(EXPO_PUSH_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Push error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}, Body: {e.response.text}")