from pydantic import BaseModel
from datetime import datetime

class AttendanceCreateDTO(BaseModel):
    competitions_id: str

class AttendanceReadDTO(BaseModel):
    id: str
    users_id: str
    competitions_id: str
    timestamp: datetime

    class Config:
        from_attributes = True