"""Schemas Pydantic para validação de dados de Planos de Acompanhamento."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class PlanoAcompanhamentoCreateSchema(BaseModel):
    """Schema de criação de plano de acompanhamento (POST)."""
    aluno_id: int
    titulo: str = Field(min_length=3, max_length=180)
    objetivo_geral: Optional[str] = None
    estrategias: Optional[str] = None
    periodicidade: Optional[str] = Field(default=None, max_length=60)
    status: Optional[str] = Field(default='ativo', max_length=30)
    data_inicio: Optional[str] = Field(default=None, description="Data de início no formato YYYY-MM-DD")
    data_fim_prevista: Optional[str] = Field(default=None, description="Data prevista de fim no formato YYYY-MM-DD")


class PlanoAcompanhamentoUpdateSchema(BaseModel):
    """Schema de atualização de plano de acompanhamento (PUT)."""
    titulo: Optional[str] = Field(default=None, min_length=3, max_length=180)
    objetivo_geral: Optional[str] = None
    estrategias: Optional[str] = None
    periodicidade: Optional[str] = Field(default=None, max_length=60)
    status: Optional[str] = Field(default=None, max_length=30)
    data_inicio: Optional[str] = Field(default=None)
    data_fim_prevista: Optional[str] = Field(default=None)
    data_fim_real: Optional[str] = Field(default=None)
