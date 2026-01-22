from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from app.database import get_db
from app.models import Container, Exercise
from app.schemas.container import ContainerReadDTO, ContainerCreateDTO
from app.logger import get_structured_logger

logger = get_structured_logger("containers_router")
router = APIRouter(prefix="/containers", tags=["containers"])


@router.get("/", response_model=List[ContainerReadDTO])
async def list_all_containers(db: Session = Depends(get_db)):
    """Lista todos os registros de containers no banco de dados."""
    try:
        containers = db.query(Container).all()
        logger.info("Consulta de lista de containers realizada", count=len(containers))
        return containers
    except SQLAlchemyError as e:
        logger.error("Erro ao listar containers no banco de dados", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao acessar a base de dados de containers")


@router.get("/{container_id}", response_model=ContainerReadDTO)
async def get_container(container_id: str, db: Session = Depends(get_db)):
    """Busca os detalhes de um registro de container específico pelo seu ID (UUID)."""
    try:
        container = db.query(Container).filter(Container.id == container_id).first()
        
        if not container:
            logger.warning("Tentativa de acesso a container inexistente", container_id=container_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de container não encontrado")
        
        return container
    except SQLAlchemyError as e:
        logger.error("Erro ao buscar container específico", container_id=container_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar consulta de container")


@router.get("/exercise/{ex_id}", response_model=ContainerReadDTO)
async def get_container_by_exercise(ex_id: str, comp_id: str, db: Session = Depends(get_db)):
    """
    Retorna o container ativo para um exercício específico
    """
    try:
        container = (db.query(Container).filter(Container.exercises_id == ex_id, Container.is_active == True).first())

        if not container:
            logger.info("Nenhum container ativo para o exercício", exercise_id=ex_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum container ativo para este exercício")
        
        return container
    except SQLAlchemyError as e:
        logger.error("Erro ao buscar container por exercício", exercise_id=ex_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao buscar estado do container")


@router.post("/", response_model=ContainerReadDTO, status_code=status.HTTP_201_CREATED)
async def create_container(exercises_id: str, payload: ContainerCreateDTO, db: Session = Depends(get_db)):
    """
    Salva os dados de um container recém-criado pelo Orchester.
    Desativa instâncias antigas do MESMO exercício para evitar conflitos.
    """
    try:
        exercise_exists = db.query(Exercise).filter(Exercise.id == exercises_id).first()

        if not exercise_exists:
            logger.error("Falha ao registrar container: Dependências não encontradas", exercise_id=exercises_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercício não encontrado")

        # Desativa apenas o container anterior DESTE exercício.
        db.query(Container).filter(Container.exercises_id == exercises_id, Container.is_active == True).update({"is_active": False})


        new_container = Container(
            exercises_id=exercises_id,
            docker_id=payload.docker_id,
            image_tag=payload.image_tag,
            port=payload.port,
            connection=payload.connection,
            is_active=True
        )
        
        db.add(new_container)
        db.commit()
        db.refresh(new_container)
        
        logger.info("Container registrado com sucesso", container_id=new_container.id, exercise_id=exercises_id)
        return new_container

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro de banco de dados ao criar container", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Não foi possível salvar o registro do container")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado no registro de container", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")


@router.delete("/{container_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_container(container_id: str, db: Session = Depends(get_db)):
    """Remove o registro de um container do banco de dados."""
    try:
        container = db.query(Container).filter(Container.id == container_id).first()
        
        if not container:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de container não encontrado")
        
        db.delete(container)
        db.commit()
        
        logger.info("Registro de container removido", container_id=container_id)
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro ao deletar container", container_id=container_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao remover registro do banco")