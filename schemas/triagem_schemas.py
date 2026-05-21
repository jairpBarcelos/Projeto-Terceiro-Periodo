"""Schemas Pydantic para validação de dados de Triagens e Avaliações."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class TriagemCreateSchema(BaseModel):
    """Schema de criação de triagem/atendimento (POST)."""
    aluno_id: int
    data_registro: str = Field(min_length=10, max_length=10, description="Data no formato YYYY-MM-DD")
    tipo_registro: str = Field(min_length=2, max_length=30, description="Tipo de registro (ex: triagem, atendimento, evolucao)")
    status: Optional[str] = Field(default='aguardando_entrevista', max_length=30)
    queixa_principal: Optional[str] = Field(default=None, max_length=2000)
    descricao: Optional[str] = None
    evolucao: Optional[str] = None
    observacoes: Optional[str] = None
    avaliacoes_json: Optional[dict] = Field(
        default=None,
        description="Checklists por categoria: {cognitiva, pedagogica, comportamental, socioemocional}"
    )


class TriagemUpdateSchema(BaseModel):
    """Schema de atualização de triagem/atendimento (PUT)."""
    data_registro: Optional[str] = Field(default=None, min_length=10, max_length=10)
    tipo_registro: Optional[str] = Field(default=None, min_length=2, max_length=30)
    status: Optional[str] = Field(default=None, max_length=30)
    queixa_principal: Optional[str] = Field(default=None, max_length=2000)
    descricao: Optional[str] = None
    evolucao: Optional[str] = None
    observacoes: Optional[str] = None
    avaliacoes_json: Optional[dict] = None
