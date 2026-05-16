"""Schemas Pydantic para validação de dados de Encaminhamentos."""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class EncaminhamentoCreateSchema(BaseModel):
    """Schema de criação de encaminhamento (POST)."""
    aluno_id: int
    tipo: str = Field(min_length=2, max_length=20, description="'interno' ou 'externo'")
    destino: str = Field(min_length=2, max_length=140)
    prioridade: str = Field(min_length=2, max_length=10, description="'alta', 'media' ou 'baixa'")
    descricao: str = Field(min_length=5)
    prazo_retorno: Optional[str] = Field(default=None, description="Data no formato YYYY-MM-DD")


class EncaminhamentoUpdateSchema(BaseModel):
    """Schema de atualização de encaminhamento (PUT) — todos os campos opcionais."""
    tipo: Optional[str] = Field(default=None, min_length=2, max_length=20)
    destino: Optional[str] = Field(default=None, min_length=2, max_length=140)
    prioridade: Optional[str] = Field(default=None, min_length=2, max_length=10)
    descricao: Optional[str] = Field(default=None, min_length=5)
    status: Optional[str] = Field(default=None, max_length=30)
    prazo_retorno: Optional[str] = Field(default=None)


class EncaminhamentoRetornoSchema(BaseModel):
    """Schema para registrar retorno/conclusão de um encaminhamento."""
    data_retorno: str = Field(description="Data no formato YYYY-MM-DD")
    observacao_retorno: Optional[str] = None
    status: Optional[str] = Field(default='concluido', max_length=30)
