from pydantic import BaseModel

class TagBase(BaseModel):
    name: str

class TagCreateDTO(TagBase):
    pass

class TagReadDTO(TagBase):
    id: str

    class Config:
        from_attributes = True