from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)   # ← agregado
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(String)  # 'admin' o 'cobrador'

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String, nullable=True)
    route = Column(String, nullable=True)
    daily_quota = Column(Float)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    description = Column(String, nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    client = relationship("Client")