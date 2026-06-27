from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    description: str

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None