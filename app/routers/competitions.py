from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from app.database import get_db
from app.models import Competition, User
from app.schemas.competition import CompetitionCreateDTO, CompetitionReadDTO, CompetitionJoinDTO, CompetitionUpdateDTO
from app.schemas.user import UserReadDTO
from app.schemas.exercise import ExerciseReadDTO
from app.logger import get_structured_logger

logger = get_structured_logger("competitions_router")
router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.get("/", response_model=List[CompetitionReadDTO])
async def list_competitions(db: Session = Depends(get_db)):
    """Lista todas as competições cadastradas no sistema."""
    try:
        competitions = db.query(Competition).all()
        logger.info("Consulta de lista de competições realizada", count=len(competitions))
        return competitions
    except SQLAlchemyError as e:
        logger.error("Erro ao listar competições", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao acessar a base de dados de competições")


@router.get("/{comp_id}", response_model=CompetitionReadDTO)
async def get_competition(comp_id: str, db: Session = Depends(get_db)):
    """Busca os detalhes de uma competição específica pelo seu ID."""
    try:
        competition = db.query(Competition).filter(Competition.id == comp_id).first()
        
        if not competition:
            logger.warning("Tentativa de acesso a competição inexistente", competition_id=comp_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competição não encontrada")
        
        return competition
    except SQLAlchemyError as e:
        logger.error("Erro ao buscar competição específica", competition_id=comp_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar consulta de competição")


@router.get("/code/{invite_code}", response_model=CompetitionReadDTO)
async def get_competition_by_code(invite_code: str, db: Session = Depends(get_db)):
    """Busca uma competição pelo código de convite."""
    try:
        competition = (db.query(Competition).filter(Competition.invite_code == invite_code).first())
        
        if not competition:
            logger.warning("Tentativa de acesso com código de convite inválido", invite_code=invite_code)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competição não encontrada")
        
        return competition
    except SQLAlchemyError as e:
        logger.error("Erro ao buscar competição por código", invite_code=invite_code, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar consulta de competição")


@router.get("/{comp_id}/participants", response_model=List[UserReadDTO])
async def list_competition_participants(comp_id: str, db: Session = Depends(get_db)):
    """Lista todos os usuários (participantes individuais) inscritos em uma competição."""
    try:
        competition = db.query(Competition).filter(Competition.id == comp_id).first()
        
        if not competition:
            logger.warning("Tentativa de listar participantes de competição inexistente", competition_id=comp_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competição não encontrada")

        logger.info("Lista de participantes consultada", competition_id=comp_id, count=len(competition.users))
        return competition.users
    except SQLAlchemyError as e:
        logger.error("Erro ao listar participantes", competition_id=comp_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar consulta de participantes")


@router.post("/join")
async def join_competition(payload: CompetitionJoinDTO, user_id: str, db: Session = Depends(get_db)):
    """Permite que um usuário entre em uma competição individualmente usando o código de convite."""
    try:
        competition = (db.query(Competition).filter(Competition.invite_code == payload.invite_code).first())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not competition:
            logger.warning("Tentativa de ingresso com código inválido", invite_code=payload.invite_code)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código de convite inválido ou competição inexistente")
        
        if not user:
            logger.warning("Tentativa de ingresso de usuário inexistente", user_id=user_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        if user not in competition.users:
            competition.users.append(user)
            db.commit()
            logger.info("Usuário entrou na competição com sucesso", user_id=user_id, username=user.username, competition_id=competition.id, competition_name=competition.name)
        else:
            logger.info("Usuário já estava inscrito na competição", user_id=user_id, competition_id=competition.id)
        
        return {"message": f"Você entrou na competição {competition.name} com sucesso!"}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro ao processar ingresso na competição", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar ingresso na competição")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado ao processar ingresso", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")


@router.get("/{comp_id}/exercises", response_model=List[ExerciseReadDTO])
async def list_competition_exercises(comp_id: str, db: Session = Depends(get_db)):
    """Lista todos os exercícios vinculados a uma competição específica."""
    try:
        competition = db.query(Competition).filter(Competition.id == comp_id).first()
        
        if not competition:
            logger.warning("Tentativa de listar exercícios de competição inexistente", competition_id=comp_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competição não encontrada")
        
        logger.info("Lista de exercícios consultada", competition_id=comp_id, count=len(competition.exercises))
        return competition.exercises
    except SQLAlchemyError as e:
        logger.error("Erro ao listar exercícios", competition_id=comp_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar consulta de exercícios")


@router.post("/", response_model=CompetitionReadDTO, status_code=status.HTTP_201_CREATED)
async def create_competition(payload: CompetitionCreateDTO, db: Session = Depends(get_db)):
    """Cria uma nova competição no sistema."""
    try:
        invite_code_exists = (db.query(Competition).filter(Competition.invite_code == payload.invite_code).first())
        if invite_code_exists:
            logger.warning("Tentativa de criação com código de convite duplicado", invite_code=payload.invite_code)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código de convite já existe")

        new_competition = Competition(**payload.model_dump())
        db.add(new_competition)
        db.commit()
        db.refresh(new_competition)
        
        logger.info("Nova competição criada com sucesso", competition_id=new_competition.id, name=new_competition.name)
        return new_competition

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro de banco de dados ao criar competição", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Não foi possível criar a competição")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado ao criar competição", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")


@router.patch("/{comp_id}", response_model=CompetitionReadDTO)
async def update_competition(comp_id: str, payload: CompetitionUpdateDTO, db: Session = Depends(get_db)):
    """Atualiza os dados de uma competição existente."""
    try:
        competition = db.query(Competition).filter(Competition.id == comp_id).first()
        
        if not competition:
            logger.warning("Tentativa de atualização de competição inexistente", competition_id=comp_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competição não encontrada")
        
        update_data = payload.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(competition, key, value)
        
        db.commit()
        db.refresh(competition)
        
        logger.info("Competição atualizada com sucesso", competition_id=comp_id)
        return competition

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro de banco de dados ao atualizar competição", competition_id=comp_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao atualizar a competição")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado ao atualizar competição", competition_id=comp_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")


@router.delete("/{comp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competition(comp_id: str, db: Session = Depends(get_db)):
    """Remove uma competição do sistema."""
    try:
        competition = db.query(Competition).filter(Competition.id == comp_id).first()
        
        if not competition:
            logger.warning("Tentativa de exclusão de competição inexistente", competition_id=comp_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competição não encontrada")
        
        db.delete(competition)
        db.commit()
        
        logger.info("Competição removida com sucesso", competition_id=comp_id)
        return None

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro ao deletar competição", competition_id=comp_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao remover competição do banco")