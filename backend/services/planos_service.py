"""Camada de serviço para operações de Planos de Acompanhamento."""
from __future__ import annotations

from datetime import date, datetime
from flask import request
from sqlalchemy import or_, func

from backend.extensions import db
from backend.models import Aluno, PlanoAcompanhamento, Usuario
from backend.services.audit import registrar_atividade


def serializar_plano(plano: PlanoAcompanhamento) -> dict:
    """Converte um objeto PlanoAcompanhamento em dict para resposta JSON."""
    return {
        'id': plano.id,
        'aluno_id': plano.aluno_id,
        'aluno_nome': plano.aluno.nome_completo if plano.aluno else None,
        'psicopedagogo_id': plano.psicopedagogo_id,
        'psicopedagogo_nome': plano.psicopedagogo.nome_completo if plano.psicopedagogo else None,
        'titulo': plano.titulo,
        'objetivo_geral': plano.objetivo_geral,
        'estrategias': plano.estrategias,
        'periodicidade': plano.periodicidade,
        'status': plano.status,
        'data_inicio': plano.data_inicio.isoformat() if plano.data_inicio else None,
        'data_fim_prevista': plano.data_fim_prevista.isoformat() if plano.data_fim_prevista else None,
        'data_fim_real': plano.data_fim_real.isoformat() if plano.data_fim_real else None,
        'created_at': plano.created_at.isoformat() if plano.created_at else None,
        'updated_at': plano.updated_at.isoformat() if plano.updated_at else None,
    }


def criar_plano_service(payload: dict, psicopedagogo_id: int) -> PlanoAcompanhamento:
    """Cria um novo plano de acompanhamento psicopedagógico."""
    aluno = Aluno.query.get_or_404(payload['aluno_id'])
    psicopedagogo = Usuario.query.get_or_404(psicopedagogo_id)

    # Validação multi-tenant: O aluno deve pertencer à mesma unidade do psicopedagogo
    if psicopedagogo.perfil and psicopedagogo.perfil.nome != 'administrador':
        if aluno.unidade_id != psicopedagogo.unidade_id:
            raise ValueError('O aluno selecionado não pertence à sua unidade escolar.')

    data_ini = None
    if payload.get('data_inicio'):
        data_ini = date.fromisoformat(payload['data_inicio'])
    else:
        data_ini = date.today()

    data_prev = None
    if payload.get('data_fim_prevista'):
        data_prev = date.fromisoformat(payload['data_fim_prevista'])

    plano = PlanoAcompanhamento(
        aluno_id=payload['aluno_id'],
        psicopedagogo_id=psicopedagogo_id,
        titulo=payload['titulo'].strip(),
        objetivo_geral=payload.get('objetivo_geral', '').strip() or None,
        estrategias=payload.get('estrategias', '').strip() or None,
        periodicidade=payload.get('periodicidade', '').strip() or None,
        status=payload.get('status', 'ativo').strip(),
        data_inicio=data_ini,
        data_fim_prevista=data_prev,
    )

    db.session.add(plano)
    db.session.commit()
    return plano


def buscar_plano_service(plano_id: int, unidade_id: int | None = None) -> PlanoAcompanhamento:
    """Busca um plano por ID e valida multi-tenant se unidade_id for fornecido."""
    plano = PlanoAcompanhamento.query.get_or_404(plano_id)
    if unidade_id and plano.aluno.unidade_id != unidade_id:
        raise ValueError('Acesso não autorizado a este plano de acompanhamento.')
    return plano


def listar_planos_service(
    psicopedagogo_id: int | None,
    status: str | None,
    q: str,
    page: int,
    limit: int,
    unidade_id: int | None = None,
) -> dict:
    """Lista planos de acompanhamento com paginação, filtros e controle multi-tenant."""
    query = (
        PlanoAcompanhamento.query
        .join(Aluno, PlanoAcompanhamento.aluno_id == Aluno.id)
        .join(Usuario, PlanoAcompanhamento.psicopedagogo_id == Usuario.id)
    )

    if psicopedagogo_id:
        query = query.filter(PlanoAcompanhamento.psicopedagogo_id == psicopedagogo_id)

    if unidade_id:
        query = query.filter(Aluno.unidade_id == unidade_id)

    if status:
        query = query.filter(PlanoAcompanhamento.status == status)

    if q:
        termo = f'%{q.lower()}%'
        query = query.filter(
            or_(
                func.lower(Aluno.nome_completo).like(termo),
                func.lower(PlanoAcompanhamento.titulo).like(termo),
                func.lower(PlanoAcompanhamento.objetivo_geral).like(termo),
            )
        )

    total = query.count()
    planos = (
        query
        .order_by(PlanoAcompanhamento.data_inicio.desc(), PlanoAcompanhamento.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        'items': [serializar_plano(p) for p in planos],
        'total': total,
        'page': page,
        'limit': limit,
    }


def obter_dashboard_planos_service(unidade_id: int | None = None) -> dict:
    """Retorna contadores de planos de acompanhamento por unidade."""
    query_base = PlanoAcompanhamento.query

    if unidade_id:
        query_base = query_base.join(Aluno).filter(Aluno.unidade_id == unidade_id)

    total = query_base.count()
    ativos = query_base.filter(PlanoAcompanhamento.status == 'ativo').count()
    concluidos = query_base.filter(PlanoAcompanhamento.status == 'concluido').count()
    suspensos = query_base.filter(PlanoAcompanhamento.status == 'suspenso').count()

    return {
        'total': total,
        'ativos': ativos,
        'concluidos': concluidos,
        'suspensos': suspensos,
    }


def registrar_atividade_plano(usuario_id: int, acao: str, plano: PlanoAcompanhamento) -> None:
    """Registra ação de auditoria para plano de acompanhamento."""
    registrar_atividade(
        usuario_id,
        acao,
        'plano_acompanhamento',
        plano.id,
        detalhes={
            'aluno_id': plano.aluno_id,
            'titulo': plano.titulo,
            'status': plano.status,
        },
        ip_origem=request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()
