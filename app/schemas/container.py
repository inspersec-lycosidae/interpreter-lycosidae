from typing import Optional
from pydantic import BaseModel

class ContainerReadDTO(BaseModel):
    id: str
    exercises_id: str
    docker_id: str
    connection: str
    port: int
    is_active: bool

    class Config:
        from_attributes = True

class ContainerInternalDTO(BaseModel):
    """
    Usado pelo Orchester para reportar o status do container criado.
    """

    docker_id: str
    image_tag: str
    port: int
    connection: str

class ContainerRequestDTO(BaseModel):
    """
    O que o Frontend envia para o Backend.
    """
    exercises_id: str
    competitions_id: str