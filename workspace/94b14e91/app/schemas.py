from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
class UserBase(BaseModel):
    username: str
    full_name: str
    role: str
class UserCreate(UserBase):
    password: str
class UserOut(UserBase):
    id: int
    class Config:
        from_attributes = True
class Token(BaseModel):
    access_token: str
    token_type: str
class PaymentCreate(BaseModel):
    user_id: int
    amount: float
    description: Optional[str] = None
class PaymentOut(BaseModel):
    id: int
    amount: float
    date: datetime
    user_id: int
    description: Optional[str]
    class Config:
        from_attributes = True