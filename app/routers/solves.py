from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from app.database import get_db
from app.models import Solve, Exercise
from app.schemas.solve import SolveSubmitDTO, SolveResponseDTO, SolveReadDTO
from app.logger import get_structured_logger

logger = get_structured_logger("solves_router")
router = APIRouter(prefix="/solves", tags=["solves"])

@router.get("/{user_id}", response_model=List[SolveReadDTO])
async def get_user_solves(user_id: str, db: Session = Depends(get_db)):
    """Recupera o histórico de resoluções de um usuário específico."""
    try:
        solves = db.query(Solve).filter(Solve.users_id == user_id).all()
        logger.info("Consulta de resoluções realizada", user_id=user_id, count=len(solves))
        return solves
    except SQLAlchemyError as e:
        logger.error("Erro ao buscar resoluções do usuário", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao acessar o histórico de resoluções")

@router.post("/submit", response_model=SolveResponseDTO)
async def submit_flag(payload: SolveSubmitDTO, users_id: str, db: Session = Depends(get_db)):
    """
    Valida a submissão de uma flag e registra a pontuação caso esteja correta.
    Possui proteções contra submissões duplicadas e validação de estado do exercício.
    """
    try:
        exercise = db.query(Exercise).filter(Exercise.id == payload.exercises_id).first()
        
        if not exercise or not exercise.is_active:
            logger.warning("Tentativa de submissão para exercício inválido ou inativo", exercise_id=payload.exercises_id, user_id=users_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercício não encontrado ou não está aceitando submissões")

        if payload.content.strip() != exercise.flag:
            logger.info("Flag incorreta submetida", user_id=users_id, exercise_id=exercise.id)
            return SolveResponseDTO(success=False, message="Flag incorreta", points_awarded=0)

        already_solved = db.query(Solve).filter(
            Solve.users_id == users_id,
            Solve.exercises_id == payload.exercises_id,
            Solve.competitions_id == payload.competitions_id
        ).first()

        if already_solved:
            logger.info("Flag correta submetida para exercício já resolvido", user_id=users_id, exercise_id=exercise.id)
            return SolveResponseDTO(success=True, message="Flag correta! (Você já resolveu este desafio anteriormente)", points_awarded=0)

        new_solve = Solve(
            users_id=users_id,
            competitions_id=payload.competitions_id,
            exercises_id=payload.exercises_id,
            points_awarded=exercise.points,
            content=payload.content.strip()
        )
        
        db.add(new_solve)
        db.commit()
        db.refresh(new_solve)
        
        logger.info("Desafio resolvido com sucesso", user_id=users_id, exercise_id=exercise.id, points=exercise.points)
        
        return SolveResponseDTO(success=True, message="Parabéns! Flag aceita.", points_awarded=exercise.points)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro de banco de dados ao processar submissão", user_id=users_id, exercise_id=payload.exercises_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar a submissão no banco de dados")
    except Exception as e:
        db.rollback()
        logger.critical("Erro fatal na submissão de flag", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno inesperado no sistema")