"""Schemas Pydantic para validação de dados de Relatórios Técnicos."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class RelatorioCreateSchema(BaseModel):
    """Schema de criação de relatório (POST)."""
    aluno_id: int
    tipo: str = Field(min_length=2, max_length=40, description="Tipo do relatório (ex: parecer, laudo, evolutivo)")
    titulo: str = Field(min_length=3, max_length=180)
    conteudo: Optional[str] = None
    status: Optional[str] = Field(default='rascunho', max_length=20, description="'rascunho' ou 'emitido'")
    ano_referencia: Optional[int] = Field(default=None, ge=2000, le=2100)
    periodo_inicio: Optional[str] = Field(default=None, description="Data inicial no formato YYYY-MM-DD")
    periodo_fim: Optional[str] = Field(default=None, description="Data final no formato YYYY-MM-DD")


class RelatorioUpdateSchema(BaseModel):
    """Schema de atualização de relatório (PUT)."""
    tipo: Optional[str] = Field(default=None, min_length=2, max_length=40)
    titulo: Optional[str] = Field(default=None, min_length=3, max_length=180)
    conteudo: Optional[str] = None
    status: Optional[str] = Field(default=None, max_length=20)
    ano_referencia: Optional[int] = Field(default=None, ge=2000, le=2100)
    periodo_inicio: Optional[str] = Field(default=None)
    periodo_fim: Optional[str] = Field(default=None)
