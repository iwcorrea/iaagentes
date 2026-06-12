from pydantic import BaseModel
from typing import Optional, Dict
class TokenRegister(BaseModel):
    token: str
    user_id: Optional[int] = None
class NotificationRequest(BaseModel):
    token: str
    title: str
    body: str
    data: Dict = {}
class UserCreate(BaseModel):
    email: str
    password: str
class UserOut(BaseModel):
    id: int
    email: str
    class Config:
        from_attributes = True