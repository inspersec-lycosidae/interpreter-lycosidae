from typing import Optional, List
from pydantic import BaseModel
from app.schemas.tag import TagReadDTO

class ExerciseBase(BaseModel):
    name: str
    description: Optional[str] = None
    difficulty: str
    points: int
    tags: List[TagReadDTO] = []

class ExerciseCreateDTO(ExerciseBase):
    flag: str
    is_active: bool = True

class ExerciseUpdateDTO(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    points: Optional[int] = None
    flag: Optional[str] = None
    is_active: Optional[bool] = None

class ExerciseReadDTO(ExerciseBase):
    """
    Não inclui a flag nem metadados sensíveis.
    """

    id: str
    is_active: bool

    class Config:
        from_attributes = True

class ExerciseAdminReadDTO(ExerciseReadDTO):
    """
    Inclui a flag para conferência.
    """
    
    flag: str