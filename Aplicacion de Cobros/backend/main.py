from fastapi import FastAPI
from .database import engine, Base
from .routers import notifications
from fastapi.middleware.cors import CORSMiddleware
import os
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Apicobros API")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(notifications.router)
@app.get("/")
def root():
    return {"message": "Apicobros Backend Running"}