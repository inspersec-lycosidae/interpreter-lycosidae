from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List

from app.database import get_db
from app.models import Competition, User, Solve
from app.schemas.scoreboard import ScoreboardEntryDTO
from app.logger import get_structured_logger

logger = get_structured_logger("scoreboard_router")
router = APIRouter(prefix="/scoreboard", tags=["scoreboard"])

@router.get("/{comp_id}", response_model=List[ScoreboardEntryDTO])
async def get_scoreboard(comp_id: str, db: Session = Depends(get_db)):
    """
    Retorna o placar de uma competição específica, calculando a pontuação 
    individual através da soma dos 'solves'.
    """
    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competição não encontrada")

    total_score_expr = func.coalesce(func.sum(Solve.points_awarded), 0)

    results = db.query(
        User.id,
        User.username,
        total_score_expr.label("total_score")
    ).join(User.competitions) \
     .outerjoin(Solve, (Solve.users_id == User.id) & (Solve.competitions_id == comp_id)) \
     .filter(Competition.id == comp_id) \
     .group_by(User.id) \
     .order_by(total_score_expr.desc()) \
     .all()

    scoreboard = []
    for index, (user_id, username, total_score) in enumerate(results):
        scoreboard.append(ScoreboardEntryDTO(
            rank=index + 1,
            username=username,
            score=int(total_score),
            users_id=user_id
        ))
        
    return scoreboard