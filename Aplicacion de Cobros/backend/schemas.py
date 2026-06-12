from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ─── USUARIO ───
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

# ─── TOKEN ───
class Token(BaseModel):
    access_token: str
    token_type: str

# ─── CLIENTE ───
class ClientBase(BaseModel):
    name: str
    phone: Optional[str] = None
    route: Optional[str] = None
    daily_quota: float

class ClientCreate(ClientBase):
    pass

class ClientOut(ClientBase):
    id: int
    class Config:
        from_attributes = True

# ─── PAGO ───
class PaymentBase(BaseModel):
    amount: float
    description: Optional[str] = None

class PaymentCreate(PaymentBase):
    client_id: int

class PaymentOut(PaymentBase):
    id: int
    date: datetime
    client_id: int
    class Config:
        from_attributes = True

# ─── NOTIFICACIÓN ───
class NotificationCreate(BaseModel):
    user_id: int
    message: str

class NotificationOut(NotificationCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True