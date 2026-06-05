CODIGO_COMPLETO
from fastapi import FastAPI
from backend.auth import app as auth_app

app = FastAPI()

app.mount("/auth", auth_app)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI backend!"}