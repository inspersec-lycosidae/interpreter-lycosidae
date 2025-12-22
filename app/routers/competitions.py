from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Competition, User
from app.schemas.competition import CompetitionCreateDTO, CompetitionReadDTO, CompetitionJoinDTO, CompetitionUpdateDTO
from app.schemas.team import TeamReadDTO
from app.schemas.exercise import ExerciseReadDTO
from app.logger import get_structured_logger

logger = get_structured_logger("competitions_router")
router = APIRouter(prefix="/competitions", tags=["competitions"])

@router.get("/", response_model=List[CompetitionReadDTO])
async def list_competitions(db: Session = Depends(get_db)):
    return db.query(Competition).all()

@router.get("/{comp_id}", response_model=CompetitionReadDTO)
async def get_competition(comp_id: str, db: Session = Depends(get_db)):
    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competição não encontrada")
    return comp

@router.get("/{comp_id}/teams", response_model=List[TeamReadDTO])
async def list_competition_teams(comp_id: str, db: Session = Depends(get_db)):
    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competição não encontrada")

    for team in comp.teams:
        team.members_ids = [user.id for user in team.users]

    return comp.teams

@router.get("/{comp_id}/exercises", response_model=List[ExerciseReadDTO])
async def list_competition_exercises(comp_id: str, db: Session = Depends(get_db)):
    """
    Lista todos os exercícios vinculados a uma competição específica
    """
    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competição não encontrada")
    
    return comp.exercises

@router.post("/", response_model=CompetitionReadDTO, status_code=201)
async def create_competition(payload: CompetitionCreateDTO, db: Session = Depends(get_db)):
    if db.query(Competition).filter(Competition.invite_code == payload.invite_code).first():
        raise HTTPException(status_code=400, detail="Invite code já existe")

    new_comp = Competition(**payload.model_dump(), status="created")
    db.add(new_comp)
    db.commit()
    db.refresh(new_comp)
    return new_comp

@router.patch("/{comp_id}", response_model=CompetitionReadDTO)
async def update_competition(comp_id: str, payload: CompetitionUpdateDTO, db: Session = Depends(get_db)):
    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    if not comp: raise HTTPException(404, "Competição não encontrada")
    
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(comp, key, value)
    
    db.commit()
    db.refresh(comp)
    return comp

@router.delete("/{comp_id}", status_code=204)
async def delete_competition(comp_id: str, db: Session = Depends(get_db)):
    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    if not comp: raise HTTPException(404, "Competição não encontrada")
    db.delete(comp)
    db.commit()
    return None