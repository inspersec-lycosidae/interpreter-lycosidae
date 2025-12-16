from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

# Interno
from app.database import get_db
from app.models import (
    Exercise, Solve, Team, UserTeam, Container, ExerciseCompetition
)
from app.schemas import (
    ExerciseCreateDTO, ExerciseReadDTO, SolveSubmitDTO, 
    SolveResponseDTO, ExerciseConnectionDTO
)
from app.logger import get_structured_logger

logger = get_structured_logger("exercises_router")

router = APIRouter(
    prefix="/exercises",
    tags=["exercises"]
)

# --- ADMINISTRAÇÃO ---
@router.post("/", response_model=ExerciseReadDTO, status_code=201)
async def create_exercise(payload: ExerciseCreateDTO, db: Session = Depends(get_db)):
    """
    Cria um novo exercício na biblioteca (Admin)
    """

    new_ex = Exercise(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        difficulty=payload.difficulty,
        points=payload.points,
        flag=payload.flag,
        image_tag=payload.image_tag,
        is_active=payload.is_active
    )

    db.add(new_ex)
    db.commit()
    db.refresh(new_ex)

    return new_ex

@router.post("/{ex_id}/link-competition/{comp_id}")
async def link_exercise_to_competition(ex_id: str, comp_id: str, db: Session = Depends(get_db)):
    """
    Adiciona um exercício da biblioteca a uma competição específica
    """

    link = ExerciseCompetition(exercise_id=ex_id, competition_id=comp_id)
    db.add(link)
    db.commit()

    return {"message": "Exercício adicionado à competição"}


# --- JOGABILIDADE (ALUNOS) ---
@router.get("/competition/{comp_id}", response_model=List[ExerciseReadDTO])
async def list_exercises_for_competition(comp_id: str, user_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Lista todos os exercícios ativos de uma competição.
    Se user_id for passado, marca quais ele já resolveu (solved_by_me).
    """

    # 1. Busca exercícios ligados à competição
    exercises = db.query(Exercise)\
        .join(ExerciseCompetition)\
        .filter(ExerciseCompetition.competition_id == comp_id)\
        .filter(Exercise.is_active == True)\
        .all()
    
    # 2. Converte para DTO e verifica solves se necessário
    result = []
    solved_ids = set()
    
    if user_id:
        # Otimização: Busca todos os solves do usuário nesta competição de uma vez
        solves = db.query(Solve.exercise_id)\
            .join(Team)\
            .filter(Team.competition_id == comp_id)\
            .filter(Solve.user_id == user_id)\
            .all()
        solved_ids = {s[0] for s in solves}

    for ex in exercises:
        dto = ExerciseReadDTO(
            id=ex.id,
            name=ex.name,
            description=ex.description,
            category=ex.category,
            difficulty=ex.difficulty,
            points=ex.points,
            solved_by_me=(ex.id in solved_ids)
        )
        result.append(dto)
        
    return result

@router.get("/{ex_id}/connection", response_model=ExerciseConnectionDTO)
async def get_exercise_connection(ex_id: str, db: Session = Depends(get_db)):
    """
    Retorna dados de conexão (IP/Porta) se houver container ativo.
    """

    container = db.query(Container).filter(
        Container.exercise_id == ex_id,
        Container.is_active == True
    ).first()
    
    if not container:
        return ExerciseConnectionDTO(has_container=False)
    
    return ExerciseConnectionDTO(
        has_container=True,
        connection_command=container.connection_command,
        port=container.port_public,
        host="lycosidae.insper.edu.br"
    )

@router.post("/{ex_id}/submit", response_model=SolveResponseDTO)
async def submit_flag(ex_id: str, payload: SolveSubmitDTO, user_id: str, db: Session = Depends(get_db)):
    """
    Valida a flag e pontua o time.
    Requer user_id.
    """

    exercise = db.query(Exercise).filter(Exercise.id == ex_id).first()
    if not exercise or not exercise.is_active:
        raise HTTPException(404, "Exercício não encontrado ou inativo")

    # ------ BLINDAGEM DE CONTEXTO ------
    is_linked = db.query(ExerciseCompetition).filter(
        ExerciseCompetition.exercise_id == ex_id,
        ExerciseCompetition.competition_id == payload.competition_id
    ).first()

    if not is_linked:
        logger.warning(f"Tentativa de bypass: User {user_id} tentou pontuar ex={ex_id} na comp={payload.competition_id}")
        raise HTTPException(status_code=403, detail="Este exercício não faz parte da competição atual.")
    # -----------------------------------

    user_team_rel = db.query(UserTeam).join(Team).filter(
        UserTeam.user_id == user_id,
        Team.competition_id == payload.competition_id
    ).first()
    
    if not user_team_rel:
        raise HTTPException(400, "Você não está em um time nesta competição")
    
    team = db.query(Team).filter(Team.id == user_team_rel.team_id).first()

    if payload.flag.strip() != exercise.flag:
        logger.info(f"Flag incorreta user={user_id} ex={ex_id} flag={payload.flag}")
        return SolveResponseDTO(success=False, message="Flag incorreta", points_awarded=0)

    existing_solve = db.query(Solve).filter(
        Solve.team_id == team.id,
        Solve.exercise_id == ex_id
    ).first()
    
    if existing_solve:
        return SolveResponseDTO(success=True, message="Flag correta! (Mas você já resolveu este desafio)", points_awarded=0)

    solve = Solve(
        user_id=user_id,
        team_id=team.id,
        exercise_id=ex_id,
        points_awarded=exercise.points,
        submission_content=payload.flag
    )
    
    # Atualiza Cache de Score do Time
    team.score += exercise.points
    
    db.add(solve)
    db.commit()
    
    logger.info(f"Solve confirmado user={user_id} ex={ex_id} team={team.id}")
    
    return SolveResponseDTO(
        success=True, 
        message="Flag correta! Pontuação registrada.", 
        points_awarded=exercise.points
    )