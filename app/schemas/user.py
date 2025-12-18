from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    name: str
    surname: str
    username: str
    email: EmailStr

class UserCreateDTO(UserBase):
    password: str

class UserUpdateDTO(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserReadDTO(UserBase):
    id: str
    is_admin: bool

    class Config:
        from_attributes = True

class UserInternalDTO(UserReadDTO):
    """
    Usado apenas entre Backend e Interpreter para verificar senhas.
    """
    
    password: str