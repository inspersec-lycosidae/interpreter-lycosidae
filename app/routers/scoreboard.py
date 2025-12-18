from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Competition
from app.schemas.team import ScoreboardEntryDTO
from app.logger import get_structured_logger

logger = get_structured_logger("scoreboard_router")
router = APIRouter(prefix="/scoreboard", tags=["scoreboard"])

@router.get("/{comp_id}", response_model=List[ScoreboardEntryDTO])
async def get_scoreboard(comp_id: str, db: Session = Depends(get_db)):
    """
    Retorna o placar de uma competição específica ordenado por pontos.
    """

    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competição não encontrada")
    
    sorted_teams = sorted(
        comp.teams, 
        key=lambda t: t.score if t.score else 0, 
        reverse=True
    )
    
    scoreboard = []
    for index, team in enumerate(sorted_teams):
        scoreboard.append(ScoreboardEntryDTO(
            rank=index + 1,
            team_name=team.name,
            score=team.score if team.score else 0,
            teams_id=team.id
        ))
        
    return scoreboard