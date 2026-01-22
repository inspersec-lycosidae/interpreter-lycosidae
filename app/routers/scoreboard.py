from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
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
    try:
        competition = db.query(Competition).filter(Competition.id == comp_id).first()
        
        if not competition:
            logger.warning("Tentativa de acesso a placar de competição inexistente", competition_id=comp_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competição não encontrada")

        # Expressão para calcular a pontuação total (soma de pontos ou 0 se não houver solves)
        total_score_expr = func.coalesce(func.sum(Solve.points_awarded), 0)

        results = (db.query(User.id, User.username, total_score_expr.label("total_score"))
            .join(User.competitions)
            .outerjoin(Solve, (Solve.users_id == User.id) & (Solve.competitions_id == comp_id))
            .filter(Competition.id == comp_id)
            .group_by(User.id)
            .order_by(total_score_expr.desc())
            .all()
        )

        # Construção do placar com ranking
        scoreboard = []
        for index, (user_id, username, total_score) in enumerate(results):
            scoreboard.append(
                ScoreboardEntryDTO(
                    rank=index + 1,
                    username=username,
                    score=int(total_score),
                    users_id=user_id
                )
            )
        
        logger.info("Placar consultado com sucesso", competition_id=comp_id, participants=len(scoreboard))
        return scoreboard

    except SQLAlchemyError as e:
        logger.error("Erro ao calcular placar da competição", competition_id=comp_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar cálculo do placar")
    except Exception as e:
        logger.critical("Erro inesperado ao gerar placar", competition_id=comp_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")