"""Camada de serviço para operações CRUD de Alunos."""
from __future__ import annotations

from datetime import date, datetime, timezone

from flask import request
from sqlalchemy import or_

from backend.extensions import db
from backend.models import Aluno, CategoriaNeurodiversidade, Laudo, Unidade
from backend.services.audit import registrar_atividade


# ---------------------------------------------------------------------------
# Serialização
# ---------------------------------------------------------------------------

def serializar_aluno(aluno: Aluno) -> dict:
    """Converte um objeto Aluno em dict para resposta JSON."""
    return {
        'id': aluno.id,
        'nome_completo': aluno.nome_completo,
        'cpf': aluno.cpf,
        'data_nascimento': aluno.data_nascimento.isoformat() if aluno.data_nascimento else None,
        'endereco': aluno.endereco,
        'responsavel_nome': aluno.responsavel_nome,
        'responsavel_telefone': aluno.responsavel_telefone,
        'serie_turma': aluno.serie_turma,
        'nivel_suporte': aluno.nivel_suporte,
        'status': aluno.status,
        'unidade_id': aluno.unidade_id,
        'unidade_nome': aluno.unidade.nome if aluno.unidade else None,
        'categorias': [
            {'id': c.id, 'nome': c.nome}
            for c in (aluno.categorias or [])
        ],
        'laudos': [
            {
                'id': l.id,
                'descricao': l.descricao,
                'data_emissao': l.data_emissao.isoformat() if l.data_emissao else None,
                'profissional_responsavel': l.profissional_responsavel,
            }
            for l in (aluno.laudos or [])
        ],
        'created_at': aluno.created_at.isoformat() if aluno.created_at else None,
        'updated_at': aluno.updated_at.isoformat() if aluno.updated_at else None,
        'deleted_at': aluno.deleted_at.isoformat() if aluno.deleted_at else None,
    }


# ---------------------------------------------------------------------------
# Listagem com filtros e paginação
# ---------------------------------------------------------------------------

def listar_alunos_service(
    unidade_id: int | None,
    status: str | None,
    q: str,
    page: int,
    limit: int,
    incluir_excluidos: bool = False,
) -> dict:
    """Lista alunos com paginação, filtro por unidade, status e busca textual."""
    query = Aluno.query

    if not incluir_excluidos:
        query = query.filter(Aluno.deleted_at.is_(None))

    if unidade_id:
        query = query.filter(Aluno.unidade_id == unidade_id)

    if status:
        query = query.filter(Aluno.status == status)

    if q:
        termo = f'%{q.lower()}%'
        query = query.filter(
            or_(
                db.func.lower(Aluno.nome_completo).like(termo),
                db.func.lower(Aluno.cpf).like(termo),
                db.func.lower(Aluno.responsavel_nome).like(termo),
                db.func.lower(Aluno.serie_turma).like(termo),
            )
        )

    total = query.count()
    alunos = (
        query
        .order_by(Aluno.nome_completo.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        'items': [serializar_aluno(a) for a in alunos],
        'total': total,
        'page': page,
        'limit': limit,
    }


# ---------------------------------------------------------------------------
# Busca individual
# ---------------------------------------------------------------------------

def buscar_aluno_service(aluno_id: int) -> Aluno:
    """Busca um aluno por ID ou retorna 404."""
    return Aluno.query.get_or_404(aluno_id)


# ---------------------------------------------------------------------------
# Criação
# ---------------------------------------------------------------------------

def criar_aluno_service(payload: dict) -> Aluno:
    """Cria um novo aluno e opcionalmente associa categorias e laudo."""
    # Valida que a unidade existe
    Unidade.query.get_or_404(payload['unidade_id'])

    aluno = Aluno(
        nome_completo=str(payload['nome_completo']).strip(),
        cpf=str(payload.get('cpf', '')).strip() or None,
        data_nascimento=date.fromisoformat(payload['data_nascimento']),
        endereco=payload.get('endereco'),
        responsavel_nome=str(payload['responsavel_nome']).strip(),
        responsavel_telefone=str(payload['responsavel_telefone']).strip(),
        serie_turma=payload.get('serie_turma'),
        nivel_suporte=payload.get('nivel_suporte'),
        unidade_id=payload['unidade_id'],
        status=payload.get('status') or 'ativo',
    )

    # Associa categorias de neurodiversidade
    categoria_ids = payload.get('categoria_ids') or []
    if categoria_ids:
        categorias = CategoriaNeurodiversidade.query.filter(
            CategoriaNeurodiversidade.id.in_(categoria_ids)
        ).all()
        aluno.categorias = categorias

    db.session.add(aluno)
    db.session.flush()  # gera o ID antes de criar o laudo

    # Cria laudo inicial se descrição fornecida
    laudo_descricao = payload.get('laudo_descricao')
    if laudo_descricao:
        laudo = Laudo(
            aluno_id=aluno.id,
            descricao=laudo_descricao,
        )
        db.session.add(laudo)

    db.session.commit()
    return aluno


# ---------------------------------------------------------------------------
# Atualização
# ---------------------------------------------------------------------------

def atualizar_aluno_service(aluno: Aluno, payload: dict) -> Aluno:
    """Atualiza os campos permitidos de um aluno existente."""
    campos_permitidos = [
        'nome_completo', 'cpf', 'data_nascimento', 'endereco',
        'responsavel_nome', 'responsavel_telefone', 'serie_turma',
        'nivel_suporte', 'unidade_id', 'status',
    ]

    for campo in campos_permitidos:
        if campo in payload:
            valor = payload[campo]
            if campo == 'data_nascimento' and isinstance(valor, str):
                valor = date.fromisoformat(valor)
            elif isinstance(valor, str):
                valor = valor.strip()
            setattr(aluno, campo, valor)

    # Atualiza categorias se fornecidas
    if 'categoria_ids' in payload:
        categoria_ids = payload['categoria_ids'] or []
        categorias = CategoriaNeurodiversidade.query.filter(
            CategoriaNeurodiversidade.id.in_(categoria_ids)
        ).all() if categoria_ids else []
        aluno.categorias = categorias

    db.session.commit()
    return aluno


# ---------------------------------------------------------------------------
# Soft Delete
# ---------------------------------------------------------------------------

def deletar_aluno_service(aluno: Aluno) -> Aluno:
    """Realiza soft delete no aluno (marca deleted_at)."""
    if aluno.deleted_at is None:
        aluno.deleted_at = datetime.now(timezone.utc)
        aluno.status = 'inativo'
        db.session.commit()
    return aluno


# ---------------------------------------------------------------------------
# Auditoria
# ---------------------------------------------------------------------------

def registrar_atividade_aluno(usuario_id: int, acao: str, aluno: Aluno) -> None:
    """Registra ação de auditoria vinculada a um aluno."""
    registrar_atividade(
        usuario_id,
        acao,
        'aluno',
        aluno.id,
        detalhes={'nome': aluno.nome_completo, 'cpf': aluno.cpf},
        ip_origem=request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()
