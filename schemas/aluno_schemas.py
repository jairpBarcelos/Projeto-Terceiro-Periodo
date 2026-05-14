"""Schemas Pydantic para validação de dados de Alunos."""

from typing import Optional, List
from pydantic import BaseModel, Field


class AlunoCreateSchema(BaseModel):
    """Schema de criação de aluno (POST)."""
    nome_completo: str = Field(min_length=2, max_length=150)
    cpf: Optional[str] = Field(default=None, max_length=14)
    data_nascimento: str = Field(min_length=10, max_length=10)
    endereco: Optional[str] = None
    responsavel_nome: str = Field(min_length=2, max_length=150)
    responsavel_telefone: str = Field(min_length=8, max_length=30)
    serie_turma: Optional[str] = None
    nivel_suporte: Optional[int] = Field(default=None, ge=1, le=3)
    unidade_id: int
    categoria_ids: Optional[List[int]] = None
    laudo_descricao: Optional[str] = None
    status: Optional[str] = 'ativo'


class AlunoUpdateSchema(BaseModel):
    """Schema de atualização de aluno (PUT) — todos os campos opcionais."""
    nome_completo: Optional[str] = Field(default=None, min_length=2, max_length=150)
    cpf: Optional[str] = Field(default=None, max_length=14)
    data_nascimento: Optional[str] = Field(default=None, min_length=10, max_length=10)
    endereco: Optional[str] = None
    responsavel_nome: Optional[str] = Field(default=None, min_length=2, max_length=150)
    responsavel_telefone: Optional[str] = Field(default=None, min_length=8, max_length=30)
    serie_turma: Optional[str] = None
    nivel_suporte: Optional[int] = Field(default=None, ge=1, le=3)
    unidade_id: Optional[int] = None
    categoria_ids: Optional[List[int]] = None
    laudo_descricao: Optional[str] = None
    status: Optional[str] = None
