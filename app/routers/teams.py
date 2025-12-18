from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Team, User, Competition
from app.schemas.team import TeamCreateDTO, TeamReadDTO, JoinTeamDTO, TeamUpdateDTO
from app.logger import get_structured_logger

logger = get_structured_logger("teams_router")
router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/{team_id}", response_model=TeamReadDTO)
async def get_team(team_id: str, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Time não encontrado")

    team.members_ids = [user.id for user in team.users]
    
    return team

@router.post("/competition/{comp_id}", response_model=TeamReadDTO, status_code=201)
async def create_team(comp_id: str, payload: TeamCreateDTO, db: Session = Depends(get_db)):
    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    user = db.query(User).filter(User.id == payload.creator_id).first()
    
    if not comp or not user:
        raise HTTPException(404, "Competição ou Criador não encontrado")

    new_team = Team(name=payload.name, creator_id=user.id)
    # Adiciona o time à competição e o criador ao time (Many-to-Many)
    comp.teams.append(new_team)
    new_team.users.append(user)
    
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    return new_team

@router.post("/{team_id}/join", status_code=200)
async def join_team(team_id: str, payload: JoinTeamDTO, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    user = db.query(User).filter(User.id == payload.users_id).first()
    
    if not team or not user:
        raise HTTPException(404, "Time ou Usuário não encontrado")
        
    if user in team.users:
        raise HTTPException(400, "Usuário já está no time")

    team.users.append(user)
    db.commit()
    return {"message": f"Bem-vindo ao time {team.name}"}

@router.delete("/{team_id}/leave/{user_id}", status_code=200)
async def leave_team(team_id: str, user_id: str, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    
    if not team or not user:
        raise HTTPException(404, "Time ou Usuário não encontrado")

    if user in team.users:
        team.users.remove(user)
        db.commit()
        return {"message": "Usuário removido do time"}
    raise HTTPException(400, "Usuário não pertence a este time")