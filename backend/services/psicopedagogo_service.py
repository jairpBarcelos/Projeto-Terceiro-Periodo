"""Serviço unificado para painel principal do psicopedagogo."""
from __future__ import annotations

from datetime import date
from sqlalchemy import func

from backend.extensions import db
from backend.models import Aluno, Encaminhamento, PlanoAcompanhamento, Triagem


def obter_dashboard_psicopedagogo_service(unidade_id: int | None = None) -> dict:
    """Retorna estatísticas consolidadas para o painel principal do psicopedagogo."""
    # 1. Casos em Acompanhamento (Alunos distintos com plano de acompanhamento ativo)
    query_casos = db.session.query(func.count(PlanoAcompanhamento.aluno_id.distinct()))
    if unidade_id:
        query_casos = query_casos.join(Aluno).filter(Aluno.unidade_id == unidade_id)
    casos_ativos = query_casos.filter(PlanoAcompanhamento.status == 'ativo').scalar() or 0

    # 2. Triagens Pendentes (Triagens na unidade com status 'aguardando_entrevista')
    query_triagens = Triagem.query
    if unidade_id:
        query_triagens = query_triagens.join(Aluno).filter(Aluno.unidade_id == unidade_id)
    triagens_pendentes = query_triagens.filter(Triagem.status == 'aguardando_entrevista').count()

    # 3. Planos Ativos
    query_planos = PlanoAcompanhamento.query
    if unidade_id:
        query_planos = query_planos.join(Aluno).filter(Aluno.unidade_id == unidade_id)
    planos_ativos = query_planos.filter(PlanoAcompanhamento.status == 'ativo').count()

    # 4. Atendimentos Hoje (Triagens da unidade registradas na data corrente)
    query_hoje = Triagem.query
    if unidade_id:
        query_hoje = query_hoje.join(Aluno).filter(Aluno.unidade_id == unidade_id)
    atendimentos_hoje = query_hoje.filter(Triagem.data_registro == date.today()).count()

    # 5. Encaminhamentos Abertos
    query_encaminhamentos = Encaminhamento.query
    if unidade_id:
        query_encaminhamentos = query_encaminhamentos.join(Aluno).filter(Aluno.unidade_id == unidade_id)
    encaminhamentos_abertos = query_encaminhamentos.filter(Encaminhamento.status == 'aberto').count()

    return {
        'casos_ativos': casos_ativos,
        'triagens_pendentes': triagens_pendentes,
        'planos_ativos': planos_ativos,
        'atendimentos_hoje': atendimentos_hoje,
        'encaminhamentos_abertos': encaminhamentos_abertos,
    }
