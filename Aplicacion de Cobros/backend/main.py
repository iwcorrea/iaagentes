from fastapi import FastAPI
from .database import engine, Base
from . import auth
from .routers.notifications import router as notifications_router
from .routers.clientes import router as clientes_router
from .routers.pagos import router as pagos_router
from fastapi.middleware.cors import CORSMiddleware
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Apicobros API")

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

app.include_router(auth.router)
app.include_router(notifications_router)
app.include_router(clientes_router)
app.include_router(pagos_router)

@app.get("/")
def root():
    return {"message": "Apicobros Backend Running"}