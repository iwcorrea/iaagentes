from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
class UserBase(BaseModel):
    email: EmailStr
class UserCreate(UserBase):
    password: str
class UserOut(UserBase):
    id: int
    is_active: bool
    class Config:
        from_attributes = True
class Token(BaseModel):
    access_token: str
    token_type: str
class TokenData(BaseModel):
    email: Optional[str] = None
class ProjectBase(BaseModel):
    name: str
class ProjectCreate(ProjectBase):
    pass
class ProjectOut(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True
class FileBase(BaseModel):
    filename: str
    content: str
class FileCreate(FileBase):
    project_id: int
class FileOut(FileBase):
    id: int
    project_id: int
    class Config:
        from_attributes = True
class ImprovementBase(BaseModel):
    title: str
    description: str
    status: str = "pending"
class ImprovementCreate(ImprovementBase):
    project_id: int
class ImprovementOut(ImprovementBase):
    id: int
    project_id: int
    class Config:
        from_attributes = True