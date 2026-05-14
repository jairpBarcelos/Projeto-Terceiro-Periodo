from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginSchema(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    senha: str = Field(min_length=1)


class RegisterSchema(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    email: EmailStr
    senha: str = Field(min_length=8)
    perfil_id: Optional[int] = None
    perfil_nome: Optional[str] = None
    cpf: Optional[str] = None
    matricula: Optional[str] = None
    unidade_id: Optional[int] = None
    status: Optional[str] = 'ativo'
