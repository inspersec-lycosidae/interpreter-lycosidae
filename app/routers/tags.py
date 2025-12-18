from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Tag
from app.schemas.tag import TagCreateDTO, TagReadDTO

router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("/", response_model=List[TagReadDTO])
async def list_tags(db: Session = Depends(get_db)):
    return db.query(Tag).all()

@router.post("/", response_model=TagReadDTO, status_code=201)
async def create_tag(payload: TagCreateDTO, db: Session = Depends(get_db)):
    if db.query(Tag).filter(Tag.name == payload.name).first():
        raise HTTPException(400, "Esta tag já existe")
    
    new_tag = Tag(name=payload.name)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag

@router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: str, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag: raise HTTPException(404, "Tag não encontrada")
    db.delete(tag)
    db.commit()
    return None