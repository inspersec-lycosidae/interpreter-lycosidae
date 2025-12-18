from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Container
from app.schemas.container import ContainerReadDTO, ContainerInternalDTO
from app.logger import get_structured_logger

logger = get_structured_logger("containers_router")
router = APIRouter(prefix="/containers", tags=["containers"])

@router.get("/", response_model=List[ContainerReadDTO])
async def list_all_containers(db: Session = Depends(get_db)):
    """
    Lista todos os registros de containers (instâncias ativas ou inativas) no banco de dados.
    """
    return db.query(Container).all()

@router.get("/{container_id}", response_model=ContainerReadDTO)
async def get_container(container_id: str, db: Session = Depends(get_db)):
    """
    Busca os detalhes de um registro de container específico pelo seu ID (UUID).
    """
    cont = db.query(Container).filter(Container.id == container_id).first()
    if not cont:
        logger.warning(f"Tentativa de acesso a container inexistente: {container_id}")
        raise HTTPException(status_code=404, detail="Registro de container não encontrado")
    
    return cont

@router.get("/exercise/{ex_id}", response_model=ContainerReadDTO)
async def get_container_by_exercise(ex_id: str, db: Session = Depends(get_db)):
    """
    Retorna o container ativo para um exercício específico.
    """
    
    cont = db.query(Container).filter(Container.exercises_id == ex_id, Container.is_active == True).first()
    if not cont: raise HTTPException(404, "Nenhum container ativo para este exercício")
    return cont

@router.post("/", response_model=ContainerReadDTO, status_code=201)
async def create_container(payload: ContainerInternalDTO, exercises_id: str, db: Session = Depends(get_db)):
    """
    Salva os dados de um container que o Orchester acabou de subir.
    """

    new_cont = Container(
        exercises_id=exercises_id,
        docker_id=payload.docker_id,
        image_tag=payload.image_tag,
        port=payload.port,
        connection=payload.connection,
        is_active=True
    )
    db.add(new_cont)
    db.commit()
    db.refresh(new_cont)
    return new_cont

@router.delete("/{container_id}", status_code=204)
async def remove_container(container_id: str, db: Session = Depends(get_db)):
    cont = db.query(Container).filter(Container.id == container_id).first()
    if not cont: raise HTTPException(404, "Registro de container não encontrado")
    db.delete(cont)
    db.commit()
    return None