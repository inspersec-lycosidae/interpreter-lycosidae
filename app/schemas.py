from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime

# --- USUÁRIOS ---
class UserCreateDTO(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None

class UserReadDTO(BaseModel):
    id: str
    username: str
    email: EmailStr
    phone_number: Optional[str] = None
    is_admin: bool = False

    class Config:
        from_attributes = True

class UserInternalDTO(UserReadDTO):
    """
    DTO EXCLUSIVO para uso interno (Backend <-> Interpreter).
    Contém o hash da senha para validação de login.
    NUNCA expor isso para o Frontend.
    """

    password: str


# --- COMPETIÇÕES ---
class CompetitionCreateDTO(BaseModel):
    name: str
    organizer: str
    invite_code: str
    start_date: datetime
    end_date: datetime

class CompetitionReadDTO(BaseModel):
    id: str
    name: str
    organizer: str
    start_date: datetime
    end_date: datetime
    status: str

    class Config:
        from_attributes = True

class CompetitionJoinDTO(BaseModel):
    user_id: str
    invite_code: str


# --- TIMES ---
class TeamCreateDTO(BaseModel):
    name: str
    creator_id: str

class TeamReadDTO(BaseModel):
    id: str
    name: str
    score: int
    competition_id: str

    class Config:
        from_attributes = True

class JoinTeamDTO(BaseModel):
    user_id: str

class ScoreboardEntryDTO(BaseModel):
    rank: int
    team_name: str
    score: int
    team_id: str


# --- EXERCÍCIOS E INFRAESTRUTURA ---
class ExerciseCreateDTO(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    difficulty: str
    points: int
    flag: str
    image_tag: Optional[str] = None
    is_active: bool = True

class ExerciseReadDTO(BaseModel):
    """
    O que o ALUNO vê. Sem a flag, sem dados sensíveis de infra.
    """

    id: str
    name: str
    description: Optional[str]
    category: str
    difficulty: str
    points: int
    solved_by_me: Optional[bool] = False 

    class Config:
        from_attributes = True

class ExerciseConnectionDTO(BaseModel):
    """
    Dados retornados quando o aluno pede para conectar no desafio
    """

    has_container: bool
    connection_command: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None


# --- SOLUÇÕES (FLAGS) ---
class SolveSubmitDTO(BaseModel):
    flag: str
    competition_id: str

class SolveResponseDTO(BaseModel):
    success: bool
    message: str
    points_awarded: int = 0