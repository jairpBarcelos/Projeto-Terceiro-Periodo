"""Rotas CRUD + dashboard para o módulo de Triagens."""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from schemas.triagem_schemas import TriagemCreateSchema, TriagemUpdateSchema
from backend.responses import created, error, success
from backend.security import jwt_required_any
from backend.services.triagens_service import (
    atualizar_triagem_service,
    buscar_triagem_service,
    criar_triagem_service,
    dashboard_triagens_service,
    listar_alunos_select,
    listar_triagens_service,
    registrar_atividade_triagem,
    serializar_triagem,
)


triagens_bp = Blueprint('triagens', __name__, url_prefix='/api/triagens')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@triagens_bp.get('/dashboard')
@jwt_required_any
def dashboard_triagens():
    """Retorna métricas consolidadas de triagens para o painel."""
    psico_id = request.args.get('psicopedagogo_id', type=int)
    return success(
        'Métricas de triagens carregadas com sucesso.',
        data=dashboard_triagens_service(psico_id),
    )


# ---------------------------------------------------------------------------
# Select de alunos (para o modal)
# ---------------------------------------------------------------------------

@triagens_bp.get('/alunos-select')
@jwt_required_any
def alunos_para_select():
    """Lista alunos ativos simplificados para popular o <select> do modal."""
    return success('Alunos carregados.', data={'alunos': listar_alunos_select()})


# ---------------------------------------------------------------------------
# Listagem
# ---------------------------------------------------------------------------

@triagens_bp.get('')
@jwt_required_any
def listar_triagens():
    """Lista triagens com paginação e filtros opcionais."""
    psico_id = request.args.get('psicopedagogo_id', type=int)
    status = request.args.get('status')
    q = (request.args.get('q') or '').strip()
    page = max(1, request.args.get('page', default=1, type=int))
    limit = min(max(1, request.args.get('limit', default=20, type=int)), 100)

    return success(
        'Triagens carregadas com sucesso.',
        data=listar_triagens_service(psico_id, status, q, page, limit),
    )


# ---------------------------------------------------------------------------
# Busca individual
# ---------------------------------------------------------------------------

@triagens_bp.get('/<int:triagem_id>')
@jwt_required_any
def buscar_triagem(triagem_id: int):
    """Retorna os dados completos de uma triagem por ID."""
    t = buscar_triagem_service(triagem_id)
    return success(
        'Triagem carregada com sucesso.',
        data={'item': serializar_triagem(t)},
    )


# ---------------------------------------------------------------------------
# Criação
# ---------------------------------------------------------------------------

@triagens_bp.post('')
@jwt_required_any
def criar_triagem():
    """Cadastra uma nova triagem no sistema."""
    payload = request.get_json(silent=True) or {}
    try:
        dados = TriagemCreateSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos.', 400, 'VALIDATION_ERROR', details=e.errors())

    psico_id = int(get_jwt_identity())

    try:
        t = criar_triagem_service(dados.model_dump(exclude_none=True), psico_id)
    except IntegrityError:
        return error('Não foi possível criar triagem. Verifique os dados.', 409, 'CONFLICT')
    except ValueError as exc:
        return error(str(exc), 400, 'VALIDATION_ERROR')

    registrar_atividade_triagem(psico_id, 'create', t)
    return created('Triagem criada com sucesso.', data={'item': serializar_triagem(t)})


# ---------------------------------------------------------------------------
# Atualização
# ---------------------------------------------------------------------------

@triagens_bp.put('/<int:triagem_id>')
@jwt_required_any
def atualizar_triagem(triagem_id: int):
    """Atualiza os dados de uma triagem existente."""
    t = buscar_triagem_service(triagem_id)
    payload = request.get_json(silent=True) or {}
    try:
        dados = TriagemUpdateSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos.', 400, 'VALIDATION_ERROR', details=e.errors())

    try:
        t = atualizar_triagem_service(t, dados.model_dump(exclude_none=True))
    except IntegrityError:
        return error('Não foi possível atualizar triagem.', 409, 'CONFLICT')

    usuario_id = int(get_jwt_identity())
    registrar_atividade_triagem(usuario_id, 'update', t)
    return success('Triagem atualizada com sucesso.', data={'item': serializar_triagem(t)})
