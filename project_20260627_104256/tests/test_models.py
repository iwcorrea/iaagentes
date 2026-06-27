# Import necessary modules
from pydantic import BaseModel
import pytest
class TestProductCreate(BaseModel):
    name: str
    description: str

class TestProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None