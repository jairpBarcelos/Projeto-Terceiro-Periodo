"""Rotas CRUD e dashboard para o módulo de Triagens e Avaliações com isolamento multi-tenant."""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt, get_jwt_identity
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
    obter_dashboard_triagens_service,
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
def obter_dashboard():
    """Retorna métricas consolidadas das triagens filtradas por unidade/psicopedagogo."""
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None
    psico_id = request.args.get('psicopedagogo_id', type=int)

    dados = dashboard_triagens_service(psicopedagogo_id=psico_id, unidade_id=unidade_id)
    return success('Estatísticas de triagens carregadas com sucesso.', data=dados)


# ---------------------------------------------------------------------------
# Select de alunos (para o modal)
# ---------------------------------------------------------------------------

@triagens_bp.get('/alunos-select')
@jwt_required_any
def alunos_para_select():
    """Lista alunos ativos simplificados pertencentes à mesma unidade do usuário."""
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    return success('Alunos carregados.', data={'alunos': listar_alunos_select(unidade_id)})


# ---------------------------------------------------------------------------
# Listagem
# ---------------------------------------------------------------------------

@triagens_bp.get('')
@jwt_required_any
def listar_triagens():
    """Lista triagens com paginação, filtros e controle multi-tenant."""
    status = request.args.get('status')
    tipo = request.args.get('tipo')
    q = (request.args.get('q') or '').strip()
    page = max(1, request.args.get('page', default=1, type=int))
    limit = min(max(1, request.args.get('limit', default=20, type=int)), 100)

    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None
    psico_id = request.args.get('psicopedagogo_id', type=int)

    dados = listar_triagens_service(
        psicopedagogo_id=psico_id,
        status=status,
        q=q,
        page=page,
        limit=limit,
        tipo=tipo,
        unidade_id=unidade_id,
    )
    return success('Triagens e avaliações carregadas com sucesso.', data=dados)


# ---------------------------------------------------------------------------
# Busca individual
# ---------------------------------------------------------------------------

@triagens_bp.get('/<int:triagem_id>')
@jwt_required_any
def obter_triagem(triagem_id: int):
    """Busca uma triagem por ID, validando o isolamento multi-tenant."""
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    try:
        triagem = buscar_triagem_service(triagem_id, unidade_id)
    except ValueError as exc:
        return error(str(exc), 403, 'FORBIDDEN')

    return success('Triagem carregada com sucesso.', data={'item': serializar_triagem(triagem)})


# ---------------------------------------------------------------------------
# Criação
# ---------------------------------------------------------------------------

@triagens_bp.post('')
@jwt_required_any
def criar_triagem():
    """Registra uma nova triagem ou avaliação técnica com segurança multi-tenant."""
    payload = request.get_json(silent=True) or {}
    try:
        dados = TriagemCreateSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos para triagem.', 400, 'VALIDATION_ERROR', details=e.errors())

    psicopedagogo_id = int(get_jwt_identity())

    try:
        triagem = criar_triagem_service(dados.model_dump(exclude_none=True), psicopedagogo_id)
    except ValueError as exc:
        return error(str(exc), 400, 'VALIDATION_ERROR')
    except IntegrityError:
        return error('Erro de integridade ao salvar triagem.', 409, 'CONFLICT')

    registrar_atividade_triagem(psicopedagogo_id, 'create', triagem)
    return created('Triagem/evolução registrada com sucesso.', data={'item': serializar_triagem(triagem)})


# ---------------------------------------------------------------------------
# Atualização
# ---------------------------------------------------------------------------

@triagens_bp.put('/<int:triagem_id>')
@jwt_required_any
def atualizar_triagem(triagem_id: int):
    """Atualiza uma triagem existente com validação multi-tenant."""
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    try:
        t = buscar_triagem_service(triagem_id, unidade_id)
    except ValueError as exc:
        return error(str(exc), 403, 'FORBIDDEN')

    payload = request.get_json(silent=True) or {}
    try:
        dados = TriagemUpdateSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos.', 400, 'VALIDATION_ERROR', details=e.errors())

    try:
        t = atualizar_triagem_service(t, dados.model_dump(exclude_none=True), unidade_id)
    except IntegrityError:
        return error('Não foi possível atualizar triagem.', 409, 'CONFLICT')
    except ValueError as exc:
        return error(str(exc), 403, 'FORBIDDEN')

    usuario_id = int(get_jwt_identity())
    registrar_atividade_triagem(usuario_id, 'update', t)
    return success('Triagem atualizada com sucesso.', data={'item': serializar_triagem(t)})
