"""Camada de serviço para operações de Triagens e Avaliações."""
from __future__ import annotations

from datetime import date, datetime
from flask import request
from sqlalchemy import or_, func

from backend.extensions import db
from backend.models import Aluno, Triagem, Usuario
from backend.services.audit import registrar_atividade


def serializar_triagem(triagem: Triagem) -> dict:
    """Converte um objeto Triagem em dict para resposta JSON."""
    return {
        'id': triagem.id,
        'aluno_id': triagem.aluno_id,
        'aluno_nome': triagem.aluno.nome_completo if triagem.aluno else None,
        'psicopedagogo_id': triagem.psicopedagogo_id,
        'psicopedagogo_nome': triagem.psicopedagogo.nome_completo if triagem.psicopedagogo else None,
        'data_registro': triagem.data_registro.isoformat() if triagem.data_registro else None,
        'tipo_registro': triagem.tipo_registro,
        'status': triagem.status,
        'descricao': triagem.descricao,
        'evolucao': triagem.evolucao,
        'observacoes': triagem.observacoes,
        'created_at': triagem.created_at.isoformat() if triagem.created_at else None,
        'updated_at': triagem.updated_at.isoformat() if triagem.updated_at else None,
    }


def criar_triagem_service(payload: dict, psicopedagogo_id: int) -> Triagem:
    """Cria uma nova triagem ou avaliação técnica."""
    aluno = Aluno.query.get_or_404(payload['aluno_id'])
    psicopedagogo = Usuario.query.get_or_404(psicopedagogo_id)

    # Validação multi-tenant: O aluno deve pertencer à mesma unidade do psicopedagogo
    if psicopedagogo.perfil and psicopedagogo.perfil.nome != 'administrador':
        if aluno.unidade_id != psicopedagogo.unidade_id:
            raise ValueError('O aluno selecionado não pertence à sua unidade escolar.')

    data_reg = date.today()
    if payload.get('data_registro'):
        data_reg = date.fromisoformat(payload['data_registro'])

    triagem = Triagem(
        aluno_id=payload['aluno_id'],
        psicopedagogo_id=psicopedagogo_id,
        data_registro=data_reg,
        tipo_registro=payload['tipo_registro'].strip(),
        status=payload.get('status', 'aguardando_entrevista').strip(),
        descricao=payload.get('descricao', '').strip() or None,
        evolucao=payload.get('evolucao', '').strip() or None,
        observacoes=payload.get('observacoes', '').strip() or None,
    )

    db.session.add(triagem)
    db.session.commit()
    return triagem


def buscar_triagem_service(triagem_id: int, unidade_id: int | None = None) -> Triagem:
    """Busca uma triagem por ID e valida multi-tenant se unidade_id for fornecido."""
    triagem = Triagem.query.get_or_404(triagem_id)
    if unidade_id and triagem.aluno.unidade_id != unidade_id:
        raise ValueError('Acesso não autorizado a esta triagem.')
    return triagem


def listar_triagens_service(
    psicopedagogo_id: int | None,
    tipo: str | None,
    status: str | None,
    q: str,
    page: int,
    limit: int,
    unidade_id: int | None = None,
) -> dict:
    """Lista triagens com paginação, filtros e controle multi-tenant."""
    query = (
        Triagem.query
        .join(Aluno, Triagem.aluno_id == Aluno.id)
        .join(Usuario, Triagem.psicopedagogo_id == Usuario.id)
    )

    if psicopedagogo_id:
        query = query.filter(Triagem.psicopedagogo_id == psicopedagogo_id)

    if unidade_id:
        query = query.filter(Aluno.unidade_id == unidade_id)

    if tipo:
        query = query.filter(Triagem.tipo_registro == tipo)

    if status:
        query = query.filter(Triagem.status == status)

    if q:
        termo = f'%{q.lower()}%'
        query = query.filter(
            or_(
                func.lower(Aluno.nome_completo).like(termo),
                func.lower(Triagem.descricao).like(termo),
                func.lower(Triagem.tipo_registro).like(termo),
            )
        )

    total = query.count()
    triagens = (
        query
        .order_by(Triagem.data_registro.desc(), Triagem.created_at.desc())
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


def obter_dashboard_triagens_service(unidade_id: int | None = None) -> dict:
    """Retorna contadores de triagens e avaliações por unidade."""
    query_base = Triagem.query

    if unidade_id:
        query_base = query_base.join(Aluno).filter(Aluno.unidade_id == unidade_id)

    total = query_base.count()
    aguardando = query_base.filter(Triagem.status == 'aguardando_entrevista').count()
    em_andamento = query_base.filter(Triagem.status == 'em_processo').count()
    concluidas = query_base.filter(Triagem.status == 'concluido').count()

    return {
        'total': total,
        'aguardando': aguardando,
        'em_andamento': em_andamento,
        'concluidas': concluidas,
    }


def registrar_atividade_triagem(usuario_id: int, acao: str, triagem: Triagem) -> None:
    """Registra ação de auditoria para triagem."""
    registrar_atividade(
        usuario_id,
        acao,
        'triagem',
        triagem.id,
        detalhes={
            'aluno_id': triagem.aluno_id,
            'tipo_registro': triagem.tipo_registro,
            'status': triagem.status,
        },
        ip_origem=request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()
