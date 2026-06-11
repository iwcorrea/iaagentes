from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, payments, projects
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Code Generator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(payments.router)
app.include_router(projects.router)
@app.get("/")
def root():
    return {"message": "API is running"}