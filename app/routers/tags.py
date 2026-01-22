from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from app.database import get_db
from app.models import Tag
from app.schemas.tag import TagCreateDTO, TagReadDTO
from app.logger import get_structured_logger

logger = get_structured_logger("tags_router")
router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("/", response_model=List[TagReadDTO])
async def list_tags(db: Session = Depends(get_db)):
    """Lista todas as tags cadastradas no sistema."""
    try:
        tags = db.query(Tag).all()
        logger.info("Consulta de lista de tags realizada", count=len(tags))
        return tags
    except SQLAlchemyError as e:
        logger.error("Erro ao listar tags", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao acessar a base de dados de tags")


@router.post("/", response_model=TagReadDTO, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: TagCreateDTO, db: Session = Depends(get_db)):
    """Cria uma nova tag, garantindo que não existam nomes duplicados."""
    try:
        if db.query(Tag).filter(Tag.name == payload.name).first():
            logger.warning("Tentativa de criar tag duplicada", tag_name=payload.name)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta tag já existe")
        
        new_tag = Tag(name=payload.name)
        db.add(new_tag)
        db.commit()
        db.refresh(new_tag)
        
        logger.info("Nova tag criada com sucesso", tag_id=new_tag.id, name=new_tag.name)
        return new_tag

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro de banco de dados ao criar tag", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Não foi possível criar a tag no banco de dados")


@router.patch("/{tag_id}", response_model=TagReadDTO)
async def update_tag(tag_id: str, payload: TagCreateDTO, db: Session = Depends(get_db)):
    """Atualiza o nome de uma tag existente."""
    try:
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            logger.warning("Tentativa de atualizar tag inexistente", tag_id=tag_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag não encontrada")
        
        tag.name = payload.name
        db.commit()
        db.refresh(tag)
        
        logger.info("Tag atualizada com sucesso", tag_id=tag_id, new_name=payload.name)
        return tag

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro ao atualizar tag", tag_id=tag_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar atualização da tag")


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: str, db: Session = Depends(get_db)):
    """Remove uma tag do sistema."""
    try:
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            logger.warning("Tentativa de exclusão de tag inexistente", tag_id=tag_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag não encontrada")
        
        db.delete(tag)
        db.commit()
        
        logger.info("Tag removida com sucesso", tag_id=tag_id)
        return None

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro ao deletar tag", tag_id=tag_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao remover tag do sistema")