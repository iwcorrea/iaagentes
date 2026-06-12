from fastapi import FastAPI
from .database import engine, Base
from . import auth  # Importamos el router de autenticación
from .routers import notifications  # Si existe, lo mantenemos
from fastapi.middleware.cors import CORSMiddleware
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Apicobros API")

# Configuración de CORS
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

# Incluir los routers
app.include_router(auth.router)
app.include_router(notifications.router)  # Solo si notifications.py existe

@app.get("/")
def root():
    return {"message": "Apicobros Backend Running"}