from fastapi import FastAPI
from .database import engine
from .routers import products

def main():
    app = FastAPI()
    app.include_router(products.router)
    engine.connect()
    app.run(host='0.0.0.0', port=8000)