from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SolveSubmitDTO(BaseModel):
    exercises_id: str
    competitions_id: str
    content: str

class SolveResponseDTO(BaseModel):
    success: bool
    message: str
    points_awarded: int = 0

class SolveReadDTO(BaseModel):
    id: str
    timestamp: datetime
    users_id: str
    exercises_id: str
    competitions_id: str
    points_awarded: int

    class Config:
        from_attributes = True