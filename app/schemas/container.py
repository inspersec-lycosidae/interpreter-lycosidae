from typing import Optional
from pydantic import BaseModel

class ContainerReadDTO(BaseModel):
    """
    Modelo de leitura de container.
    """
    id: str
    exercises_id: str
    docker_id: str
    connection: str
    port: int
    is_active: bool

    class Config:
        from_attributes = True

class ContainerCreateDTO(BaseModel):
    """
    Modelo para recebimento de dados de criação de container.
    """
    docker_id: str
    image_tag: str
    port: int
    connection: str
    is_active: bool = True
    exercises_id: Optional[str] = None

class ContainerInternalDTO(BaseModel):
    """
    Modelo de transferência interna para o Orchester.
    """
    docker_id: str
    image_tag: str
    port: int
    connection: str