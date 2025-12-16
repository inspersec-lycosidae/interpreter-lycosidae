from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
import hashlib
import os
import time

# Interno
from app.database import get_db
from app.models import User
from app.schemas import UserCreateDTO, UserReadDTO, UserInternalDTO
from app.logger import get_structured_logger


logger = get_structured_logger("auth_router")
PASS_SALT = os.getenv("PASS_SALT", "Lycosidae")

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

def pass_hasher(password: str) -> str:
    """
    Gera hash SHA-256 com salt
    """

    hasher = hashlib.sha256()
    hasher.update((password + PASS_SALT).encode('utf-8'))

    return hasher.hexdigest()

# Endpoints
@router.post("/register", response_model=UserReadDTO, status_code=201)
async def register(payload: UserCreateDTO, db: Session = Depends(get_db)):
    """
    Registra um novo usuário.
    Recebe senha em plaintext (do Backend), hasheia e salva.
    """

    start_time = time.time()
    logger.info("Tentativa de registro", email=payload.email, username=payload.username)

    try:
        # Verifica duplicidade de Email
        existing_email = db.query(User).filter(User.email == payload.email).first()
        if existing_email:
            raise HTTPException(
                status_code=400, 
                detail="E-mail já cadastrado"
            )

        # Verifica duplicidade de Username
        existing_user = db.query(User).filter(User.username == payload.username).first()
        if existing_user:
            raise HTTPException(
                status_code=400, 
                detail="Nome de usuário já está em uso"
            )

        # Criação do Usuário
        new_user = User(
            username=payload.username,
            email=payload.email,
            password=pass_hasher(payload.password),
            phone_number=getattr(payload, 'phone_number', None),
            is_admin=False
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        duration = time.time() - start_time
        logger.log_api_response("/auth/register", 201, {"user_id": new_user.id}, response_time=duration)

        return new_user

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error("Erro crítico no registro", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno no servidor ao criar usuário.")

@router.get("/users/email/{email}", response_model=UserInternalDTO)
async def get_user_by_email_internal(email: str, db: Session = Depends(get_db)):
    """
    Rota final: GET /auth/users/email/{email}
    Usado pelo Backend para Login. Retorna hash da senha.
    """

    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return user

@router.get("/profile/{user_id}", response_model=UserReadDTO)
async def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """
    Busca perfil público do usuário pelo ID.
    """

    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return user