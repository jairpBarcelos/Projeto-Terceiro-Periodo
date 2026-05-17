"""Camada de serviço para operações de Triagens."""
from __future__ import annotations

from datetime import date

from flask import request
from sqlalchemy import or_, func

from backend.extensions import db
from backend.models import Aluno, Triagem, Usuario
from backend.services.audit import registrar_atividade


# ---------------------------------------------------------------------------
# Serialização
# ---------------------------------------------------------------------------

def serializar_triagem(t: Triagem) -> dict:
    """Converte um objeto Triagem em dict para resposta JSON."""
    aluno = t.aluno
    psico = t.psicopedagogo
    return {
        'id': t.id,
        'aluno_id': t.aluno_id,
        'aluno_nome': aluno.nome_completo if aluno else None,
        'aluno_serie_turma': aluno.serie_turma if aluno else None,
        'aluno_responsavel': aluno.responsavel_nome if aluno else None,
        'aluno_data_nascimento': aluno.data_nascimento.isoformat() if aluno and aluno.data_nascimento else None,
        'psicopedagogo_id': t.psicopedagogo_id,
        'psicopedagogo_nome': psico.nome_completo if psico else None,
        'data_registro': t.data_registro.isoformat() if t.data_registro else None,
        'tipo_registro': t.tipo_registro,
        'status': t.status,
        'queixa_principal': t.queixa_principal,
        'descricao': t.descricao,
        'evolucao': t.evolucao,
        'observacoes': t.observacoes,
        'avaliacoes_json': t.avaliacoes_json or {},
        'created_at': t.created_at.isoformat() if t.created_at else None,
        'updated_at': t.updated_at.isoformat() if t.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Dashboard / métricas
# ---------------------------------------------------------------------------

def dashboard_triagens_service(psicopedagogo_id: int | None = None) -> dict:
    """Retorna métricas reais de triagens para o painel do psicopedagogo."""
    q = Triagem.query
    if psicopedagogo_id:
        q = q.filter(Triagem.psicopedagogo_id == psicopedagogo_id)

    total = q.count()
    aguardando = q.filter(Triagem.status == 'aguardando_entrevista').count()
    em_avaliacao = q.filter(Triagem.status == 'em_avaliacao').count()
    concluidas = q.filter(Triagem.status == 'concluida').count()
    alta_prioridade = q.filter(Triagem.status == 'alta_prioridade').count()

    return {
        'total': total,
        'aguardando_entrevista': aguardando,
        'em_avaliacao': em_avaliacao,
        'concluidas': concluidas,
        'alta_prioridade': alta_prioridade,
    }


# ---------------------------------------------------------------------------
# Listagem com filtros e paginação
# ---------------------------------------------------------------------------

def listar_triagens_service(
    psicopedagogo_id: int | None,
    status: str | None,
    q: str,
    page: int,
    limit: int,
) -> dict:
    """Lista triagens com paginação, filtros e busca textual."""
    query = (
        Triagem.query
        .join(Aluno, Triagem.aluno_id == Aluno.id)
        .join(Usuario, Triagem.psicopedagogo_id == Usuario.id)
    )

    if psicopedagogo_id:
        query = query.filter(Triagem.psicopedagogo_id == psicopedagogo_id)

    if status:
        query = query.filter(Triagem.status == status)

    if q:
        termo = f'%{q.lower()}%'
        query = query.filter(
            or_(
                func.lower(Aluno.nome_completo).like(termo),
                func.lower(Triagem.queixa_principal).like(termo),
                func.lower(Triagem.descricao).like(termo),
            )
        )

    total = query.count()
    triagens = (
        query
        .order_by(Triagem.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        'items': [serializar_triagem(t) for t in triagens],
        'total': total,
        'page': page,
        'limit': limit,
    }


# ---------------------------------------------------------------------------
# Busca individual
# ---------------------------------------------------------------------------

def buscar_triagem_service(triagem_id: int) -> Triagem:
    """Busca uma triagem por ID ou retorna 404."""
    return Triagem.query.get_or_404(triagem_id)


# ---------------------------------------------------------------------------
# Criação
# ---------------------------------------------------------------------------

def criar_triagem_service(payload: dict, psicopedagogo_id: int) -> Triagem:
    """Cria uma nova triagem vinculada ao psicopedagogo logado."""
    Aluno.query.get_or_404(payload['aluno_id'])

    t = Triagem(
        aluno_id=payload['aluno_id'],
        psicopedagogo_id=psicopedagogo_id,
        data_registro=date.fromisoformat(payload['data_registro']),
        tipo_registro=payload.get('tipo_registro', 'triagem').strip().lower(),
        status=payload.get('status', 'aguardando_entrevista').strip().lower(),
        queixa_principal=payload.get('queixa_principal', '').strip() or None,
        descricao=payload.get('descricao', '').strip() or None,
        evolucao=payload.get('evolucao', '').strip() or None,
        observacoes=payload.get('observacoes', '').strip() or None,
        avaliacoes_json=payload.get('avaliacoes_json') or {},
    )

    db.session.add(t)
    db.session.commit()
    return t


# ---------------------------------------------------------------------------
# Atualização
# ---------------------------------------------------------------------------

def atualizar_triagem_service(t: Triagem, payload: dict) -> Triagem:
    """Atualiza os campos permitidos de uma triagem."""
    campos_texto = ['tipo_registro', 'status', 'queixa_principal',
                    'descricao', 'evolucao', 'observacoes']

    for campo in campos_texto:
        if campo in payload and payload[campo] is not None:
            setattr(t, campo, str(payload[campo]).strip() or None)

    if payload.get('data_registro'):
        t.data_registro = date.fromisoformat(payload['data_registro'])

    if 'avaliacoes_json' in payload:
        t.avaliacoes_json = payload['avaliacoes_json'] or {}

    db.session.commit()
    return t


# ---------------------------------------------------------------------------
# Select de alunos (para o modal)
# ---------------------------------------------------------------------------

def listar_alunos_select() -> list:
    """Retorna lista simplificada de alunos ativos para popular o <select>."""
    alunos = (
        Aluno.query
        .filter(Aluno.status == 'ativo', Aluno.deleted_at.is_(None))
        .order_by(Aluno.nome_completo)
        .all()
    )
    return [
        {
            'id': a.id,
            'nome': a.nome_completo,
            'serie_turma': a.serie_turma or '',
            'responsavel': a.responsavel_nome,
            'data_nascimento': a.data_nascimento.isoformat() if a.data_nascimento else None,
            'unidade': a.unidade.nome if a.unidade else '',
        }
        for a in alunos
    ]


# ---------------------------------------------------------------------------
# Auditoria
# ---------------------------------------------------------------------------

def registrar_atividade_triagem(
    usuario_id: int,
    acao: str,
    t: Triagem,
) -> None:
    """Registra ação de auditoria vinculada a uma triagem."""
    registrar_atividade(
        usuario_id,
        acao,
        'triagem',
        t.id,
        detalhes={
            'aluno_id': t.aluno_id,
            'tipo_registro': t.tipo_registro,
            'status': t.status,
        },
        ip_origem=request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()
