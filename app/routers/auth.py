from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import hashlib
import os

from app.database import get_db
from app.models import User
from app.schemas.user import UserCreateDTO, UserReadDTO, UserInternalDTO, UserUpdateDTO
from app.logger import get_structured_logger

logger = get_structured_logger("auth_router")
router = APIRouter(prefix="/auth", tags=["auth"])

PASS_SALT = os.getenv("PASS_SALT", "Lycosidae")


def pass_hasher(password: str) -> str:
    """Gera hash SHA256 da senha com salt configurado."""
    hasher = hashlib.sha256()
    hasher.update((password + PASS_SALT).encode("utf-8"))
    return hasher.hexdigest()


@router.get("/users", response_model=List[UserReadDTO])
async def list_users(db: Session = Depends(get_db)):
    """Lista todos os usuários cadastrados no sistema."""
    try:
        users = db.query(User).all()
        logger.info("Consulta de lista de usuários realizada", count=len(users))
        return users
    except SQLAlchemyError as e:
        logger.error("Erro ao listar usuários", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao acessar a base de dados de usuários")


@router.get("/profile/{user_id}", response_model=UserReadDTO)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Busca os detalhes de um usuário específico pelo seu ID."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning("Tentativa de acesso a usuário inexistente", user_id=user_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        return user
    except SQLAlchemyError as e:
        logger.error("Erro ao buscar usuário específico", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar consulta de usuário")


@router.get("/user/{email}", response_model=UserInternalDTO)
async def get_user_by_email_internal(email: str, db: Session = Depends(get_db)):
    """
    Endpoint CRÍTICO para o Backend.
    Retorna os dados internos (incluindo hash da senha) para validação de login.
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            logger.warning("Tentativa de acesso a usuário inexistente por e-mail", email=email)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        return user
    except SQLAlchemyError as e:
        logger.error("Erro ao buscar usuário por e-mail", email=email, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao processar consulta de usuário")


@router.post("/register", response_model=UserReadDTO, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreateDTO, db: Session = Depends(get_db)):
    """Registra um novo usuário no sistema."""
    try:
        email_exists = db.query(User).filter(User.email == payload.email).first()
        if email_exists:
            logger.warning("Tentativa de registro com e-mail duplicado", email=payload.email)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já cadastrado")
        
        username_exists = db.query(User).filter(User.username == payload.username).first()
        if username_exists:
            logger.warning("Tentativa de registro com username duplicado", username=payload.username)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username já cadastrado")
        
        # Criação do novo usuário
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
        
        logger.info("Novo usuário registrado com sucesso", user_id=new_user.id, username=new_user.username)
        return new_user

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro de banco de dados ao registrar usuário", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Não foi possível registrar o usuário")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado no registro de usuário", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")


@router.put("/profile/{user_id}", response_model=UserReadDTO)
async def update_user(user_id: str, payload: UserUpdateDTO, db: Session = Depends(get_db)):
    """Atualiza os dados de um usuário existente."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning("Tentativa de atualização de usuário inexistente", user_id=user_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        update_data = payload.model_dump(exclude_unset=True)

        # Hash da senha se fornecida
        if update_data.get("password"):
            update_data["password"] = pass_hasher(update_data["password"])
        else:
            update_data.pop("password", None)
        
        if "email" in update_data:
            email_exists = (db.query(User).filter(User.email == update_data["email"], User.id != user_id).first())
            if email_exists:
                logger.warning("Tentativa de atualização com e-mail já em uso", user_id=user_id, email=update_data["email"])
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já está em uso")

        if "username" in update_data:
            username_exists = (db.query(User).filter(User.username == update_data["username"], User.id != user_id).first())
            if username_exists:
                logger.warning("Tentativa de atualização com username já em uso", user_id=user_id, username=update_data["username"])
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username já está em uso")

        for key, value in update_data.items():
            setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        
        logger.info("Usuário atualizado com sucesso", user_id=user_id)
        return user

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro de banco de dados ao atualizar usuário", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao atualizar o perfil")
    except Exception as e:
        db.rollback()
        logger.critical("Erro inesperado ao atualizar usuário", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no sistema")


@router.delete("/profile/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Remove um usuário do sistema."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning("Tentativa de exclusão de usuário inexistente", user_id=user_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        db.delete(user)
        db.commit()
        
        logger.info("Usuário removido com sucesso", user_id=user_id)
        return None

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro ao deletar usuário", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao remover usuário do banco")