"""Camada de serviço para operações de Encaminhamentos."""
from __future__ import annotations

from datetime import date, datetime, timezone

from flask import request
from sqlalchemy import or_, func

from backend.extensions import db
from backend.models import Aluno, Encaminhamento, Usuario
from backend.services.audit import registrar_atividade


# ---------------------------------------------------------------------------
# Serialização
# ---------------------------------------------------------------------------

def serializar_encaminhamento(enc: Encaminhamento) -> dict:
    """Converte um objeto Encaminhamento em dict para resposta JSON."""
    return {
        'id': enc.id,
        'aluno_id': enc.aluno_id,
        'aluno_nome': enc.aluno.nome_completo if enc.aluno else None,
        'solicitante_id': enc.solicitante_id,
        'solicitante_nome': enc.solicitante.nome_completo if enc.solicitante else None,
        'tipo': enc.tipo,
        'destino': enc.destino,
        'prioridade': enc.prioridade,
        'status': enc.status,
        'descricao': enc.descricao,
        'prazo_retorno': enc.prazo_retorno.isoformat() if enc.prazo_retorno else None,
        'data_retorno': enc.data_retorno.isoformat() if enc.data_retorno else None,
        'observacao_retorno': enc.observacao_retorno,
        'created_at': enc.created_at.isoformat() if enc.created_at else None,
        'updated_at': enc.updated_at.isoformat() if enc.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Dashboard / métricas
# ---------------------------------------------------------------------------

def dashboard_encaminhamentos_service(solicitante_id: int | None = None) -> dict:
    """Retorna métricas consolidadas de encaminhamentos para o painel do psicopedagogo."""
    query_base = Encaminhamento.query

    if solicitante_id:
        query_base = query_base.filter(Encaminhamento.solicitante_id == solicitante_id)

    total_abertos = query_base.filter(Encaminhamento.status == 'aberto').count()
    total_internos = query_base.filter(
        Encaminhamento.tipo == 'interno',
        Encaminhamento.status == 'aberto',
    ).count()
    total_externos = query_base.filter(
        Encaminhamento.tipo == 'externo',
        Encaminhamento.status == 'aberto',
    ).count()
    total_com_retorno = query_base.filter(
        Encaminhamento.data_retorno.isnot(None),
    ).count()
    total_sem_retorno = query_base.filter(
        Encaminhamento.data_retorno.is_(None),
        Encaminhamento.status != 'cancelado',
    ).count()

    return {
        'abertos': total_abertos,
        'internos': total_internos,
        'externos': total_externos,
        'com_retorno': total_com_retorno,
        'sem_retorno': total_sem_retorno,
    }


# ---------------------------------------------------------------------------
# Listagem com filtros e paginação
# ---------------------------------------------------------------------------

def listar_encaminhamentos_service(
    solicitante_id: int | None,
    tipo: str | None,
    status: str | None,
    q: str,
    page: int,
    limit: int,
) -> dict:
    """Lista encaminhamentos com paginação, filtros e busca textual."""
    query = (
        Encaminhamento.query
        .join(Aluno, Encaminhamento.aluno_id == Aluno.id)
        .join(Usuario, Encaminhamento.solicitante_id == Usuario.id)
    )

    if solicitante_id:
        query = query.filter(Encaminhamento.solicitante_id == solicitante_id)

    if tipo:
        query = query.filter(Encaminhamento.tipo == tipo)

    if status:
        query = query.filter(Encaminhamento.status == status)

    if q:
        termo = f'%{q.lower()}%'
        query = query.filter(
            or_(
                func.lower(Aluno.nome_completo).like(termo),
                func.lower(Encaminhamento.destino).like(termo),
                func.lower(Encaminhamento.descricao).like(termo),
            )
        )

    total = query.count()
    encaminhamentos = (
        query
        .order_by(Encaminhamento.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        'items': [serializar_encaminhamento(e) for e in encaminhamentos],
        'total': total,
        'page': page,
        'limit': limit,
    }


# ---------------------------------------------------------------------------
# Busca individual
# ---------------------------------------------------------------------------

def buscar_encaminhamento_service(enc_id: int) -> Encaminhamento:
    """Busca um encaminhamento por ID ou retorna 404."""
    return Encaminhamento.query.get_or_404(enc_id)


# ---------------------------------------------------------------------------
# Criação
# ---------------------------------------------------------------------------

def criar_encaminhamento_service(payload: dict, solicitante_id: int) -> Encaminhamento:
    """Cria um novo encaminhamento vinculado ao psicopedagogo logado."""
    # Valida que o aluno existe
    Aluno.query.get_or_404(payload['aluno_id'])

    prazo = None
    if payload.get('prazo_retorno'):
        prazo = date.fromisoformat(payload['prazo_retorno'])

    enc = Encaminhamento(
        aluno_id=payload['aluno_id'],
        solicitante_id=solicitante_id,
        tipo=payload['tipo'].strip().lower(),
        destino=payload['destino'].strip(),
        prioridade=payload['prioridade'].strip().lower(),
        descricao=payload['descricao'].strip(),
        prazo_retorno=prazo,
        status='aberto',
    )

    db.session.add(enc)
    db.session.commit()
    return enc


# ---------------------------------------------------------------------------
# Atualização
# ---------------------------------------------------------------------------

def atualizar_encaminhamento_service(enc: Encaminhamento, payload: dict) -> Encaminhamento:
    """Atualiza os campos permitidos de um encaminhamento."""
    campos_simples = ['tipo', 'destino', 'prioridade', 'descricao', 'status']

    for campo in campos_simples:
        if campo in payload and payload[campo] is not None:
            setattr(enc, campo, str(payload[campo]).strip())

    if 'prazo_retorno' in payload and payload['prazo_retorno']:
        enc.prazo_retorno = date.fromisoformat(payload['prazo_retorno'])

    db.session.commit()
    return enc


# ---------------------------------------------------------------------------
# Registro de retorno
# ---------------------------------------------------------------------------

def registrar_retorno_service(enc: Encaminhamento, payload: dict) -> Encaminhamento:
    """Registra a data e observação de retorno, encerrando o encaminhamento."""
    enc.data_retorno = date.fromisoformat(payload['data_retorno'])
    enc.observacao_retorno = payload.get('observacao_retorno', '').strip() or None
    enc.status = payload.get('status', 'concluido').strip()
    db.session.commit()
    return enc


# ---------------------------------------------------------------------------
# Auditoria
# ---------------------------------------------------------------------------

def registrar_atividade_encaminhamento(
    usuario_id: int,
    acao: str,
    enc: Encaminhamento,
) -> None:
    """Registra ação de auditoria vinculada a um encaminhamento."""
    registrar_atividade(
        usuario_id,
        acao,
        'encaminhamento',
        enc.id,
        detalhes={
            'aluno_id': enc.aluno_id,
            'destino': enc.destino,
            'tipo': enc.tipo,
            'status': enc.status,
        },
        ip_origem=request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()
