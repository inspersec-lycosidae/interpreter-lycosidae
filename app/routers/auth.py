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

@router.get("/user/{email}", response_model=UserInternalDTO)
async def get_user_by_email_internal(email: str, db: Session = Depends(get_db)):
    """
    Endpoint CRÍTICO para o Backend.
    Retorna os dados internos (incluindo hash da senha) para validação de login.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user

@router.post("/register", response_model=UserReadDTO, status_code=201)
async def register(payload: UserCreateDTO, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "E-mail já cadastrado")
    elif db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(400, "User já cadastrado")
    
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

@router.put("/profile/{user_id}", response_model=UserReadDTO)
async def update_user(user_id: str, payload: UserUpdateDTO, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: 
      raise HTTPException(404, "Usuário não encontrado")
    
    update_data = payload.model_dump(exclude_unset=True)

    if update_data.get("password"): 
        update_data["password"] = pass_hasher(update_data["password"])
    else:
        update_data.pop("password", None)
        
    if "email" in update_data:
      email_exists = db.query(User).filter(User.email == update_data["email"], User.id != user_id).first()
      if email_exists:
        raise HTTPException(400, "E-mail já está em uso")

    if "username" in update_data:
      username_exists = db.query(User).filter(User.username == update_data["username"], User.id != user_id).first()
      if username_exists:
        raise HTTPException(400, "Username já está em uso")

    for key, value in update_data.items():
      setattr(user, key, value)
    
    try:
      db.commit()
      db.refresh(user)
      return user
    except Exception as e:
      db.rollback()
      raise HTTPException(500, "Erro interno ao atualizar o perfil")

@router.delete("/profile/{user_id}", status_code=204)
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "Usuário não encontrado")
    db.delete(user)
    db.commit()
    return None