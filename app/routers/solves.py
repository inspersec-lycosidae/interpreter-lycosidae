from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Solve, Exercise
from app.schemas.solve import SolveSubmitDTO, SolveResponseDTO, SolveReadDTO
from app.logger import get_structured_logger

logger = get_structured_logger("solves_router")
router = APIRouter(prefix="/solves", tags=["solves"])

@router.get("/{user_id}", response_model=List[SolveReadDTO])
async def get_user_solves(user_id: str, db: Session = Depends(get_db)):
    return db.query(Solve).filter(Solve.users_id == user_id).all()

@router.post("/submit", response_model=SolveResponseDTO)
async def submit_flag(payload: SolveSubmitDTO, users_id: str, db: Session = Depends(get_db)):
    # 1. Valida Exercício
    ex = db.query(Exercise).filter(Exercise.id == payload.exercises_id).first()
    if not ex or not ex.is_active:
        raise HTTPException(404, "Exercício inválido ou inativo")

    # 2. Valida Flag
    if payload.content.strip() != ex.flag:
        return SolveResponseDTO(success=False, message="Flag incorreta")

    # 3. Verifica se o time já resolveu (Evita double-point)
    already_solved = db.query(Solve).filter(
        Solve.users_id == users_id,
        Solve.exercises_id == payload.exercises_id,
        Solve.competitions_id == payload.competitions_id
    ).first()

    if already_solved:
        return SolveResponseDTO(success=True, message="Flag correta! (Já resolvida)", points_awarded=0)

    # 4. Cria o registro de Solve
    new_solve = Solve(
        users_id=users_id,
        competitions_id=payload.competitions_id,
        exercises_id=payload.exercises_id,
        points_awarded=ex.points,
        content=payload.content
    )
    
    db.add(new_solve)
    db.commit()
    
    return SolveResponseDTO(success=True, message="Parabéns! Flag aceita.", points_awarded=ex.points)

