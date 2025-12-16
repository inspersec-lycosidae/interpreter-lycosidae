from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import uuid

# Interno
from app.database import get_db
from app.models import (
    Competition, Team, UserCompetition, UserTeam, User
)
from app.schemas import (
    CompetitionCreateDTO, CompetitionReadDTO, CompetitionJoinDTO,
    TeamCreateDTO, TeamReadDTO, JoinTeamDTO, ScoreboardEntryDTO
)
from app.logger import get_structured_logger

logger = get_structured_logger("competitions_router")

router = APIRouter(
    prefix="/competitions",
    tags=["competitions"]
)

# --- COMPETITIONS ---
@router.post("/", response_model=CompetitionReadDTO, status_code=201)
async def create_competition(payload: CompetitionCreateDTO, db: Session = Depends(get_db)):
    """
    Cria uma nova competição (Admin).
    """

    if db.query(Competition).filter(Competition.invite_code == payload.invite_code).first():
        raise HTTPException(status_code=400, detail="Invite code já existe")

    new_comp = Competition(
        name=payload.name,
        organizer=payload.organizer,
        invite_code=payload.invite_code,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status="created"
    )
    
    db.add(new_comp)
    db.commit()
    db.refresh(new_comp)
    
    logger.info("Competição criada", id=new_comp.id, name=new_comp.name)

    return new_comp

@router.get("/", response_model=List[CompetitionReadDTO])
async def list_competitions(db: Session = Depends(get_db)):
    """
    Lista todas as competições
    """

    return db.query(Competition).all()

@router.get("/{comp_id}", response_model=CompetitionReadDTO)
async def get_competition(comp_id: str, db: Session = Depends(get_db)):
    """
    Lista uma competição pelo seu ID
    """

    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competição não encontrada")

    return comp

@router.post("/{comp_id}/join", status_code=200)
async def join_competition(comp_id: str, payload: CompetitionJoinDTO, db: Session = Depends(get_db)):
    """
    Registra um usuário na competição se o código bater.
    """

    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competição não encontrada")
    
    # Valida Código
    if comp.invite_code != payload.invite_code:
        raise HTTPException(status_code=403, detail="Código de convite inválido")
    
    # Verifica se já está participando
    exists = db.query(UserCompetition).filter(
        UserCompetition.user_id == payload.user_id,
        UserCompetition.competition_id == comp_id
    ).first()
    
    if exists:
        return {"message": "Usuário já registrado nesta competição"}
    
    # Registra
    new_relation = UserCompetition(user_id=payload.user_id, competition_id=comp_id)
    db.add(new_relation)
    db.commit()
    
    logger.info("Usuário entrou na competição", user_id=payload.user_id, comp_id=comp_id)
    return {"message": "Registro realizado com sucesso"}


# --- TEAMS ---
@router.get("/{comp_id}/teams", response_model=List[TeamReadDTO])
async def list_teams(comp_id: str, db: Session = Depends(get_db)):
    """
    Lista times de uma competição
    """

    teams = db.query(Team).filter(Team.competition_id == comp_id).all()

    return teams

@router.post("/{comp_id}/teams", response_model=TeamReadDTO, status_code=201)
async def create_team(comp_id: str, payload: TeamCreateDTO, db: Session = Depends(get_db)):
    """
    Cria um time e adiciona o criador como membro.
    """
    
    new_team = Team(
        name=payload.name,
        creator_id=payload.creator_id,
        competition_id=comp_id,
        score=0
    )
    db.add(new_team)
    db.flush()
    
    member = UserTeam(user_id=payload.creator_id, team_id=new_team.id)
    db.add(member)
    
    db.commit()
    db.refresh(new_team)
    
    return new_team

@router.post("/teams/{team_id}/join", status_code=200)
async def join_team(team_id: str, payload: JoinTeamDTO, db: Session = Depends(get_db)):
    """
    Adiciona usuário a um time existente
    """

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(404, "Time não encontrado")
        
    # Verifica duplicidade
    if db.query(UserTeam).filter(UserTeam.user_id==payload.user_id, UserTeam.team_id==team_id).first():
        raise HTTPException(400, "Usuário já está no time")

    member = UserTeam(user_id=payload.user_id, team_id=team_id)
    db.add(member)
    db.commit()

    return {"message": f"Bem-vindo ao time {team.name}"}


# --- SCOREBOARD ---
@router.get("/{comp_id}/scoreboard", response_model=List[ScoreboardEntryDTO])
async def get_scoreboard(comp_id: str, db: Session = Depends(get_db)):
    """
    Retorna o placar ordenado por Score (DESC).
    """

    teams = db.query(Team)\
        .filter(Team.competition_id == comp_id)\
        .order_by(desc(Team.score))\
        .all()
    
    scoreboard = []
    for index, team in enumerate(teams):
        scoreboard.append({
            "rank": index + 1,
            "team_name": team.name,
            "score": team.score,
            "team_id": team.id
        })
        
    return scoreboard