from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class CompetitionBase(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime

class CompetitionCreateDTO(CompetitionBase):
    organizer: str
    invite_code: str

class CompetitionUpdateDTO(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class CompetitionReadDTO(CompetitionBase):
    id: str
    organizer: str
    invite_code: str
    status: str

    class Config:
        from_attributes = True

class CompetitionJoinDTO(BaseModel):
    invite_code: str