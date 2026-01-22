from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from app.database import get_db
from app.models import Exercise, Tag, Competition
from app.schemas.exercise import ExerciseCreateDTO, ExerciseReadDTO, ExerciseUpdateDTO, ExerciseAdminReadDTO
from app.schemas.competition import CompetitionReadDTO
from app.logger import get_structured_logger

logger = get_structured_logger("exercises_router")
router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/", response_model=List[ExerciseReadDTO])
async def list_all_exercises(db: Session = Depends(get_db)):
    """Lista todos os exercícios cadastrados no sistema."""
    try:
        exercises = db.query(Exercise).all()
        logger.info("Consulta de lista de exercícios realizada", count=len(exercises))
        return exercises
    except SQLAlchemyError as e:
        logger.error("Erro ao listar exercícios", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao acessar a base de dados de exercícios")


@router.get("/{ex_id}", response_model=ExerciseAdminReadDTO)
async def get_exercise(ex_id: str, db: Session = Depends(get_db)):
    """Busca os detalhes de um exercício específico pelo seu ID."""
    try:
        exercise = db.query(Exercise).filter(Exercise.id == ex_id).first()
        
        if not exercise:
            logger.warning("Tentativa de acesso a exercício inexistente", exercise_id=ex_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercício não encontrado")
        
        return exercise
    except SQLAlchemyError as e:
        logger.error("Erro ao buscar exercício específico", exercise_id=ex_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar consulta de exercício")


@router.post("/", response_model=ExerciseReadDTO, status_code=status.HTTP_201_CREATED)
async def create_exercise(payload: ExerciseCreateDTO, db: Session = Depends(get_db)):
    """Cria um novo exercício no sistema."""
    try:
        new_exercise = Exercise(**payload.model_dump())
        db.add(new_exercise)
        db.commit()
        db.refresh(new_exercise)
        
        logger.info("Novo exercício criado com sucesso", exercise_id=new_exercise.id, name=new_exercise.name)
        return new_exercise

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro de banco de dados ao criar exercício", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Não foi possível criar o exercício")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado ao criar exercício", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")


@router.post("/{ex_id}/competition/{comp_id}")
async def link_exercise_to_competition(ex_id: str, comp_id: str, db: Session = Depends(get_db)):
    """Vincula um exercício a uma competição específica."""
    try:
        exercise = db.query(Exercise).filter(Exercise.id == ex_id).first()
        competition = db.query(Competition).filter(Competition.id == comp_id).first()
        
        if not exercise or not competition:
            logger.warning("Tentativa de vinculação com recursos inexistentes", exercise_id=ex_id, competition_id=comp_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercício ou Competição não encontrados")
        
        if exercise not in competition.exercises:
            competition.exercises.append(exercise)
            db.commit()
            logger.info("Exercício vinculado à competição com sucesso", exercise_id=ex_id, competition_id=comp_id)
        else:
            logger.info("Exercício já estava vinculado à competição", exercise_id=ex_id, competition_id=comp_id)
        
        return {"message": "Exercício vinculado à competição"}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro ao vincular exercício à competição", exercise_id=ex_id, competition_id=comp_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar vinculação")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado ao vincular exercício", exercise_id=ex_id, competition_id=comp_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")


@router.post("/{ex_id}/tags/{tag_id}")
async def link_exercise_to_tag(ex_id: str, tag_id: str, db: Session = Depends(get_db)):
    """Vincula uma tag a um exercício específico."""
    try:
        exercise = db.query(Exercise).filter(Exercise.id == ex_id).first()
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        
        if not exercise or not tag:
            logger.warning("Tentativa de vinculação com recursos inexistentes", exercise_id=ex_id, tag_id=tag_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercício ou Tag não encontrados")
        
        if tag not in exercise.tags:
            exercise.tags.append(tag)
            db.commit()
            logger.info("Tag vinculada ao exercício com sucesso", exercise_id=ex_id, tag_id=tag_id)
        else:
            logger.info("Tag já estava vinculada ao exercício", exercise_id=ex_id, tag_id=tag_id)
        
        return {"message": "Tag vinculada com sucesso"}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro ao vincular tag ao exercício", exercise_id=ex_id, tag_id=tag_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar vinculação")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado ao vincular tag", exercise_id=ex_id, tag_id=tag_id,error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")


@router.get("/{ex_id}/competitions", response_model=List[CompetitionReadDTO])
async def list_exercise_competitions(ex_id: str, db: Session = Depends(get_db)):
    """Lista todas as competições às quais um exercício está vinculado."""
    try:
        exercise = db.query(Exercise).filter(Exercise.id == ex_id).first()
        
        if not exercise:
            logger.warning("Tentativa de listar competições de exercício inexistente", exercise_id=ex_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercício não encontrado")
        
        logger.info("Lista de competições do exercício consultada", exercise_id=ex_id, count=len(exercise.competitions))
        return exercise.competitions
    except SQLAlchemyError as e:
        logger.error("Erro ao listar competições do exercício", exercise_id=ex_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar consulta de competições")


@router.patch("/{ex_id}", response_model=ExerciseReadDTO)
async def update_exercise(ex_id: str, payload: ExerciseUpdateDTO, db: Session = Depends(get_db)):
    """Atualiza os dados de um exercício existente."""
    try:
        exercise = db.query(Exercise).filter(Exercise.id == ex_id).first()
        
        if not exercise:
            logger.warning("Tentativa de atualização de exercício inexistente", exercise_id=ex_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercício não encontrado")
        
        update_data = payload.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(exercise, key, value)
        
        db.commit()
        db.refresh(exercise)
        
        logger.info("Exercício atualizado com sucesso", exercise_id=ex_id)
        return exercise

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro de banco de dados ao atualizar exercício", exercise_id=ex_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao atualizar o exercício")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado ao atualizar exercício", exercise_id=ex_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")


@router.delete("/{ex_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(ex_id: str, db: Session = Depends(get_db)):
    """Remove um exercício do sistema."""
    try:
        exercise = db.query(Exercise).filter(Exercise.id == ex_id).first()
        
        if not exercise:
            logger.warning("Tentativa de exclusão de exercício inexistente", exercise_id=ex_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercício não encontrado")
        
        db.delete(exercise)
        db.commit()
        
        logger.info("Exercício removido com sucesso", exercise_id=ex_id)
        return None

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro ao deletar exercício", exercise_id=ex_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao remover exercício do banco")


@router.delete("/{ex_id}/competition/{comp_id}")
async def unlink_exercise_from_competition(ex_id: str, comp_id: str, db: Session = Depends(get_db)):
    """Remove o vínculo entre um exercício e uma competição."""
    try:
        exercise = db.query(Exercise).filter(Exercise.id == ex_id).first()
        competition = db.query(Competition).filter(Competition.id == comp_id).first()
        
        if not exercise or not competition:
            logger.warning("Tentativa de desvinculação com recursos inexistentes", exercise_id=ex_id, competition_id=comp_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercício ou Competição não encontrados")
        
        if exercise in competition.exercises:
            competition.exercises.remove(exercise)
            db.commit()
            logger.info("Exercício desvinculado da competição com sucesso", exercise_id=ex_id, competition_id=comp_id)
        else:
            logger.info("Exercício já não estava vinculado à competição", exercise_id=ex_id, competition_id=comp_id)
        
        return {"message": "Vínculo removido com sucesso"}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro ao desvincular exercício da competição", exercise_id=ex_id, competition_id=comp_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar desvinculação")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado ao desvincular exercício", exercise_id=ex_id, competition_id=comp_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")


@router.delete("/{ex_id}/tags/{tag_id}")
async def unlink_exercise_from_tag(ex_id: str, tag_id: str, db: Session = Depends(get_db)):
    """Remove o vínculo entre um exercício e uma tag."""
    try:
        exercise = db.query(Exercise).filter(Exercise.id == ex_id).first()
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        
        if not exercise or not tag:
            logger.warning("Tentativa de desvinculação com recursos inexistentes", exercise_id=ex_id, tag_id=tag_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercício ou Tag não encontrados")
        
        if tag in exercise.tags:
            exercise.tags.remove(tag)
            db.commit()
            logger.info("Tag desvinculada do exercício com sucesso", exercise_id=ex_id, tag_id=tag_id)
        else:
            logger.info("Tag já não estava vinculada ao exercício", exercise_id=ex_id, tag_id=tag_id)
        
        return {"message": "Tag desvinculada com sucesso"}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro ao desvincular tag do exercício", exercise_id=ex_id, tag_id=tag_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar desvinculação")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado ao desvincular tag", exercise_id=ex_id, tag_id=tag_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")