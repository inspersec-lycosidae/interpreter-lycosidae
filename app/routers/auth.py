from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
import hashlib
import os

from app.database import get_db
from app.models import User
from app.schemas.user import UserCreateDTO, UserReadDTO, UserInternalDTO, UserUpdateDTO
from app.logger import get_structured_logger

logger = get_structured_logger("auth_router")
PASS_SALT = os.getenv("PASS_SALT", "Lycosidae")

router = APIRouter(prefix="/auth", tags=["auth"])

def pass_hasher(password: str) -> str:
    hasher = hashlib.sha256()
    hasher.update((password + PASS_SALT).encode('utf-8'))
    return hasher.hexdigest()

@router.get("/users", response_model=list[UserReadDTO])
async def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/profile/{user_id}", response_model=UserReadDTO)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "Usuário não encontrado")
    return user

@router.post("/register", response_model=UserReadDTO, status_code=201)
async def register(payload: UserCreateDTO, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "E-mail já cadastrado")
    
    new_user = User(
        name=payload.name,
        surname=payload.surname,
        username=payload.username,
        email=payload.email,
        password=pass_hasher(payload.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.patch("/profile/{user_id}", response_model=UserReadDTO)
async def update_user(user_id: str, payload: UserUpdateDTO, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "Usuário não encontrado")
    
    update_data = payload.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = pass_hasher(update_data["password"])
        
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/profile/{user_id}", status_code=204)
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "Usuário não encontrado")
    db.delete(user)
    db.commit()
    return None