"""Camada de serviço para operações de Triagens e Avaliações."""
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

def serializar_triagem(triagem: Triagem) -> dict:
    """Converte um objeto Triagem em dict para resposta JSON."""
    aluno = triagem.aluno
    psico = triagem.psicopedagogo
    return {
        'id': triagem.id,
        'aluno_id': triagem.aluno_id,
        'aluno_nome': aluno.nome_completo if aluno else None,
        'aluno_serie_turma': aluno.serie_turma if aluno else None,
        'aluno_responsavel': aluno.responsavel_nome if aluno else None,
        'aluno_data_nascimento': aluno.data_nascimento.isoformat() if aluno and aluno.data_nascimento else None,
        'psicopedagogo_id': triagem.psicopedagogo_id,
        'psicopedagogo_nome': psico.nome_completo if psico else None,
        'data_registro': triagem.data_registro.isoformat() if triagem.data_registro else None,
        'tipo_registro': triagem.tipo_registro,
        'status': triagem.status,
        'queixa_principal': triagem.queixa_principal,
        'descricao': triagem.descricao,
        'evolucao': triagem.evolucao,
        'observacoes': triagem.observacoes,
        'avaliacoes_json': triagem.avaliacoes_json or {},
        'created_at': triagem.created_at.isoformat() if triagem.created_at else None,
        'updated_at': triagem.updated_at.isoformat() if triagem.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Dashboard / métricas
# ---------------------------------------------------------------------------

def dashboard_triagens_service(psicopedagogo_id: int | None = None, unidade_id: int | None = None) -> dict:
    """Retorna métricas reais de triagens para o painel do psicopedagogo."""
    q = Triagem.query
    if psicopedagogo_id:
        q = q.filter(Triagem.psicopedagogo_id == psicopedagogo_id)
    if unidade_id:
        q = q.join(Aluno).filter(Aluno.unidade_id == unidade_id)

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


# ---------------------------------------------------------------------------
# Listagem com filtros e paginação
# ---------------------------------------------------------------------------

def listar_triagens_service(
    psicopedagogo_id: int | None,
    status: str | None,
    q: str,
    page: int,
    limit: int,
    tipo: str | None = None,
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
                func.lower(Triagem.queixa_principal).like(termo),
                func.lower(Triagem.descricao).like(termo),
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


# ---------------------------------------------------------------------------
# Busca individual
# ---------------------------------------------------------------------------

def buscar_triagem_service(triagem_id: int, unidade_id: int | None = None) -> Triagem:
    """Busca uma triagem por ID e valida multi-tenant se unidade_id for fornecido."""
    triagem = Triagem.query.get_or_404(triagem_id)
    if unidade_id and triagem.aluno.unidade_id != unidade_id:
        raise ValueError('Acesso não autorizado a esta triagem.')
    return triagem


# ---------------------------------------------------------------------------
# Criação
# ---------------------------------------------------------------------------

def criar_triagem_service(payload: dict, psicopedagogo_id: int) -> Triagem:
    """Cria uma nova triagem vinculada ao psicopedagogo logado com validação multi-tenant."""
    aluno = Aluno.query.get_or_404(payload['aluno_id'])
    psicopedagogo = Usuario.query.get_or_404(psicopedagogo_id)

    # Validação multi-tenant: O aluno deve pertencer à mesma unidade do psicopedagogo
    if psicopedagogo.perfil and psicopedagogo.perfil.nome != 'administrador':
        if aluno.unidade_id != psicopedagogo.unidade_id:
            raise ValueError('O aluno selecionado não pertence à sua unidade escolar.')

    data_reg = date.today()
    if payload.get('data_registro'):
        data_reg = date.fromisoformat(payload['data_registro'])

    t = Triagem(
        aluno_id=payload['aluno_id'],
        psicopedagogo_id=psicopedagogo_id,
        data_registro=data_reg,
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

def atualizar_triagem_service(t: Triagem, payload: dict, unidade_id: int | None = None) -> Triagem:
    """Atualiza os campos permitidos de uma triagem, validando multi-tenant."""
    if unidade_id and t.aluno.unidade_id != unidade_id:
        raise ValueError('Acesso não autorizado para atualizar esta triagem.')

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

def listar_alunos_select(unidade_id: int | None = None) -> list:
    """Retorna lista simplificada de alunos ativos para popular o <select> do modal, isolando por unidade."""
    q = Aluno.query.filter(Aluno.status == 'ativo', Aluno.deleted_at.is_(None))
    if unidade_id:
        q = q.filter(Aluno.unidade_id == unidade_id)

    alunos = q.order_by(Aluno.nome_completo).all()
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
