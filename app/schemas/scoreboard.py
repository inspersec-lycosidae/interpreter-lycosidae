from pydantic import BaseModel

class ScoreboardEntryDTO(BaseModel):
    rank: int
    username: str
    score: int
    users_id: str