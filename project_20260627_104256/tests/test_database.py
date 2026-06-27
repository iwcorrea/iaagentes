# Import necessary modules
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.models.product import Product
import pytest

declarative_base() -> Base = declarative_base(name='Product')

class TestProduct(Base):
    __tablename__ = 'test_products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String)