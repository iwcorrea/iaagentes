from fastapi import FastAPI
from .database import engine, Base
from . import auth
from .routers import notifications
from .routers import clientes
from .routers import pagos
from fastapi.middleware.cors import CORSMiddleware
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Apicobros API")

# CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
if ALLOWED_ORIGINS != "*":
    ALLOWED_ORIGINS = ALLOWED_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(notifications.router)
app.include_router(clientes.router)
app.include_router(pagos.router)

@app.get("/")
def root():
    return {"message": "Apicobros Backend Running"}