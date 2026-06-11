from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Project, File, Improvement, User
from ..schemas import ProjectCreate, ProjectOut, FileOut, ImprovementOut
from ..auth import get_current_user
router = APIRouter(prefix="/projects", tags=["projects"])
def get_user_id_from_email(email: str, db: Session):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id
@router.get("/", response_model=List[ProjectOut])
def list_projects(email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = get_user_id_from_email(email, db)
    return db.query(Project).filter(Project.owner_id == user_id).all()
@router.post("/", response_model=ProjectOut)
def create_project(project: ProjectCreate, email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = get_user_id_from_email(email, db)
    db_project = Project(name=project.name, owner_id=user_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project
@router.delete("/{id}")
def delete_project(id: int, email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = get_user_id_from_email(email, db)
    project = db.query(Project).filter(Project.id == id, Project.owner_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}
@router.get("/{id}/files", response_model=List[FileOut])
def get_project_files(id: int, email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = get_user_id_from_email(email, db)
    project = db.query(Project).filter(Project.id == id, Project.owner_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    return project.files
@router.get("/{id}/files/{file_id}", response_model=FileOut)
def get_file(id: int, file_id: int, email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = get_user_id_from_email(email, db)
    project = db.query(Project).filter(Project.id == id, Project.owner_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    file = db.query(File).filter(File.id == file_id, File.project_id == id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file
@router.post("/{id}/execute")
def execute_project(id: int, email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = get_user_id_from_email(email, db)
    project = db.query(Project).filter(Project.id == id, Project.owner_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    return {"output": "Execution successful: Hello World!"}
@router.get("/{id}/improvements", response_model=List[ImprovementOut])
def get_improvements(id: int, email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = get_user_id_from_email(email, db)
    project = db.query(Project).filter(Project.id == id, Project.owner_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    return project.improvements
@router.patch("/improvements/{id}")
def update_improvement(id: int, status: str, email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = get_user_id_from_email(email, db)
    improvement = db.query(Improvement).join(Project).filter(Improvement.id == id, Project.owner_id == user_id).first()
    if not improvement:
        raise HTTPException(status_code=404, detail="Improvement not found or unauthorized")
    improvement.status = status
    db.commit()
    return {"message": "Updated"}