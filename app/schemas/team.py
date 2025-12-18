from typing import Optional, List
from pydantic import BaseModel

class TeamBase(BaseModel):
    name: str

class TeamCreateDTO(TeamBase):
    creator_id: str

class TeamReadDTO(TeamBase):
    id: str
    creator_id: str
    score: int = 0
    members_ids: Optional[List[str]] = []

    class Config:
        from_attributes = True

class JoinTeamDTO(BaseModel):
    users_id: str
    teams_id: Optional[str] = None

class TeamUpdateDTO(BaseModel):
    name: Optional[str] = None

class ScoreboardEntryDTO(BaseModel):
    rank: int
    team_name: str
    score: int
    teams_id: str