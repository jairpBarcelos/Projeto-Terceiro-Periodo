"""Rotas para o módulo de Planos de Acompanhamento."""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt, get_jwt_identity
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from schemas.plano_schemas import PlanoAcompanhamentoCreateSchema, PlanoAcompanhamentoUpdateSchema
from backend.responses import created, error, success
from backend.security import jwt_required_any
from backend.services.planos_service import (
    buscar_plano_service,
    criar_plano_service,
    listar_planos_service,
    obter_dashboard_planos_service,
    registrar_atividade_plano,
    serializar_plano,
)


planos_bp = Blueprint('planos', __name__, url_prefix='/api/planos')


@planos_bp.get('/dashboard')
@jwt_required_any
def obter_dashboard():
    """Retorna métricas consolidadas de planos de acompanhamento."""
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    dados = obter_dashboard_planos_service(unidade_id)
    return success('Estatísticas de planos carregadas com sucesso.', data=dados)


@planos_bp.get('')
@jwt_required_any
def listar_planos():
    """Lista planos de acompanhamento com filtros, paginação e controle multi-tenant."""
    status = request.args.get('status')
    q = (request.args.get('q') or '').strip()
    page = max(1, request.args.get('page', default=1, type=int))
    limit = min(max(1, request.args.get('limit', default=20, type=int)), 100)

    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    dados = listar_planos_service(
        psicopedagogo_id=None,
        status=status,
        q=q,
        page=page,
        limit=limit,
        unidade_id=unidade_id,
    )
    return success('Planos de acompanhamento carregados com sucesso.', data=dados)


@planos_bp.get('/<int:plano_id>')
@jwt_required_any
def obter_plano(plano_id: int):
    """Busca um plano por ID, validando isolamento de escola (multi-tenant)."""
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    try:
        plano = buscar_plano_service(plano_id, unidade_id)
    except ValueError as exc:
        return error(str(exc), 403, 'FORBIDDEN')

    return success('Plano de acompanhamento carregado com sucesso.', data={'item': serializar_plano(plano)})


@planos_bp.post('')
@jwt_required_any
def criar_plano():
    """Cadastra um novo plano de acompanhamento psicopedagógico."""
    payload = request.get_json(silent=True) or {}
    try:
        dados = PlanoAcompanhamentoCreateSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos para plano.', 400, 'VALIDATION_ERROR', details=e.errors())

    psicopedagogo_id = int(get_jwt_identity())

    try:
        plano = criar_plano_service(dados.model_dump(exclude_none=True), psicopedagogo_id)
    except ValueError as exc:
        return error(str(exc), 400, 'VALIDATION_ERROR')
    except IntegrityError:
        return error('Erro de integridade ao salvar plano.', 409, 'CONFLICT')

    registrar_atividade_plano(psicopedagogo_id, 'create', plano)
    return created('Plano de acompanhamento criado com sucesso.', data={'item': serializar_plano(plano)})
