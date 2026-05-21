"""Rotas para o módulo de Triagens e Avaliações."""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt, get_jwt_identity
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from schemas.triagem_schemas import TriagemCreateSchema, TriagemUpdateSchema
from backend.responses import created, error, success
from backend.security import jwt_required_any
from backend.services.triagens_service import (
    buscar_triagem_service,
    criar_triagem_service,
    listar_triagens_service,
    obter_dashboard_triagens_service,
    registrar_atividade_triagem,
    serializar_triagem,
)


triagens_bp = Blueprint('triagens', __name__, url_prefix='/api/triagens')


@triagens_bp.get('/dashboard')
@jwt_required_any
def obter_dashboard():
    """Retorna métricas consolidadas das triagens."""
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    dados = obter_dashboard_triagens_service(unidade_id)
    return success('Estatísticas de triagens carregadas com sucesso.', data=dados)


@triagens_bp.get('')
@jwt_required_any
def listar_triagens():
    """Lista triagens com filtros, paginação e controle multi-tenant."""
    tipo = request.args.get('tipo')
    status = request.args.get('status')
    q = (request.args.get('q') or '').strip()
    page = max(1, request.args.get('page', default=1, type=int))
    limit = min(max(1, request.args.get('limit', default=20, type=int)), 100)

    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    dados = listar_triagens_service(
        psicopedagogo_id=None,
        tipo=tipo,
        status=status,
        q=q,
        page=page,
        limit=limit,
        unidade_id=unidade_id,
    )
    return success('Triagens e avaliações carregadas com sucesso.', data=dados)


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


@triagens_bp.post('')
@jwt_required_any
def criar_triagem():
    """Registra uma nova triagem ou evolução técnica."""
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
