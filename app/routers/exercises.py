from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Exercise, Tag, Competition
from app.schemas.exercise import ExerciseCreateDTO, ExerciseReadDTO, ExerciseUpdateDTO, ExerciseAdminReadDTO
from app.logger import get_structured_logger

logger = get_structured_logger("exercises_router")
router = APIRouter(prefix="/exercises", tags=["exercises"])

@router.get("/", response_model=List[ExerciseReadDTO])
async def list_all_exercises(db: Session = Depends(get_db)):
    return db.query(Exercise).all()

@router.get("/{ex_id}", response_model=ExerciseAdminReadDTO)
async def get_exercise(ex_id: str, db: Session = Depends(get_db)):
    ex = db.query(Exercise).filter(Exercise.id == ex_id).first()
    if not ex: raise HTTPException(404, "Exercício não encontrado")
    return ex

@router.post("/", response_model=ExerciseReadDTO, status_code=201)
async def create_exercise(payload: ExerciseCreateDTO, db: Session = Depends(get_db)):
    new_ex = Exercise(**payload.model_dump())
    db.add(new_ex)
    db.commit()
    db.refresh(new_ex)
    logger.info("Novo exercício criado", id=new_ex.id, name=new_ex.name)
    return new_ex

@router.post("/{ex_id}/competition/{comp_id}")
async def link_exercise_to_competition(ex_id: str, comp_id: str, db: Session = Depends(get_db)):
    ex = db.query(Exercise).filter(Exercise.id == ex_id).first()
    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    
    if not ex or not comp:
        raise HTTPException(404, "Exercício ou Competição não encontrada")
    
    if ex not in comp.exercises:
        comp.exercises.append(ex)
        db.commit()
    return {"message": "Exercício vinculado à competição"}

@router.post("/{ex_id}/tags/{tag_id}")
async def link_exercise_to_tag(ex_id: str, tag_id: str, db: Session = Depends(get_db)):
    ex = db.query(Exercise).filter(Exercise.id == ex_id).first()
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not ex or not tag:
        raise HTTPException(404, "Exercício ou Tag não encontrada")
    
    if tag not in ex.tags:
        ex.tags.append(tag)
        db.commit()
    return {"message": "Tag vinculada com sucesso"}

@router.patch("/{ex_id}", response_model=ExerciseReadDTO)
async def update_exercise(ex_id: str, payload: ExerciseUpdateDTO, db: Session = Depends(get_db)):
    ex = db.query(Exercise).filter(Exercise.id == ex_id).first()
    if not ex: raise HTTPException(404, "Exercício não encontrado")
    
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(ex, key, value)
    
    db.commit()
    db.refresh(ex)
    return ex

@router.delete("/{ex_id}", status_code=204)
async def delete_exercise(ex_id: str, db: Session = Depends(get_db)):
    ex = db.query(Exercise).filter(Exercise.id == ex_id).first()
    if not ex: raise HTTPException(404, "Exercício não encontrado")
    db.delete(ex)
    db.commit()
    return None
