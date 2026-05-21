"""Rotas CRUD + dashboard para o módulo de Encaminhamentos."""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt, get_jwt_identity
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from schemas.encaminhamento_schemas import (
    EncaminhamentoCreateSchema,
    EncaminhamentoRetornoSchema,
    EncaminhamentoUpdateSchema,
)
from backend.responses import created, error, success
from backend.security import jwt_required_any
from backend.services.encaminhamentos_service import (
    atualizar_encaminhamento_service,
    buscar_encaminhamento_service,
    criar_encaminhamento_service,
    dashboard_encaminhamentos_service,
    listar_encaminhamentos_service,
    registrar_atividade_encaminhamento,
    registrar_retorno_service,
    serializar_encaminhamento,
)


encaminhamentos_bp = Blueprint('encaminhamentos', __name__, url_prefix='/api/encaminhamentos')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@encaminhamentos_bp.get('/dashboard')
@jwt_required_any
def dashboard_encaminhamentos():
    """Retorna métricas consolidadas de encaminhamentos para o painel."""
    solicitante_id = request.args.get('solicitante_id', type=int)
    
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    return success(
        'Métricas de encaminhamentos carregadas com sucesso.',
        data=dashboard_encaminhamentos_service(solicitante_id, unidade_id),
    )


# ---------------------------------------------------------------------------
# Listagem
# ---------------------------------------------------------------------------

@encaminhamentos_bp.get('')
@jwt_required_any
def listar_encaminhamentos():
    """Lista encaminhamentos com paginação e filtros opcionais."""
    solicitante_id = request.args.get('solicitante_id', type=int)
    tipo = request.args.get('tipo')
    status = request.args.get('status')
    q = (request.args.get('q') or '').strip()
    page = max(1, request.args.get('page', default=1, type=int))
    limit = min(max(1, request.args.get('limit', default=20, type=int)), 100)

    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    return success(
        'Encaminhamentos carregados com sucesso.',
        data=listar_encaminhamentos_service(solicitante_id, tipo, status, q, page, limit, unidade_id),
    )


# ---------------------------------------------------------------------------
# Busca individual
# ---------------------------------------------------------------------------

@encaminhamentos_bp.get('/<int:enc_id>')
@jwt_required_any
def buscar_encaminhamento(enc_id: int):
    """Retorna os dados completos de um encaminhamento por ID."""
    enc = buscar_encaminhamento_service(enc_id)

    # Validação multi-tenant: O aluno associado deve pertencer à mesma unidade do usuário logado (a menos que seja admin)
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id')
    if perfil != 'administrador' and enc.aluno and enc.aluno.unidade_id != unidade_id:
        return error('Acesso não autorizado a este encaminhamento.', 403, 'FORBIDDEN')

    return success(
        'Encaminhamento carregado com sucesso.',
        data={'item': serializar_encaminhamento(enc)},
    )


# ---------------------------------------------------------------------------
# Criação
# ---------------------------------------------------------------------------

@encaminhamentos_bp.post('')
@jwt_required_any
def criar_encaminhamento():
    """Cadastra um novo encaminhamento no sistema."""
    payload = request.get_json(silent=True) or {}
    try:
        dados = EncaminhamentoCreateSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos.', 400, 'VALIDATION_ERROR', details=e.errors())

    solicitante_id = int(get_jwt_identity())

    try:
        enc = criar_encaminhamento_service(dados.model_dump(exclude_none=True), solicitante_id)
    except IntegrityError:
        return error('Não foi possível criar encaminhamento. Verifique os dados.', 409, 'CONFLICT')
    except ValueError as exc:
        return error(str(exc), 400, 'VALIDATION_ERROR')

    registrar_atividade_encaminhamento(solicitante_id, 'create', enc)
    return created('Encaminhamento criado com sucesso.', data={'item': serializar_encaminhamento(enc)})


# ---------------------------------------------------------------------------
# Atualização
# ---------------------------------------------------------------------------

@encaminhamentos_bp.put('/<int:enc_id>')
@jwt_required_any
def atualizar_encaminhamento(enc_id: int):
    """Atualiza os dados de um encaminhamento existente."""
    enc = buscar_encaminhamento_service(enc_id)

    # Validação multi-tenant: O aluno associado deve pertencer à mesma unidade do usuário logado (a menos que seja admin)
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id')
    if perfil != 'administrador' and enc.aluno and enc.aluno.unidade_id != unidade_id:
        return error('Acesso não autorizado a este encaminhamento.', 403, 'FORBIDDEN')

    payload = request.get_json(silent=True) or {}
    try:
        dados = EncaminhamentoUpdateSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos.', 400, 'VALIDATION_ERROR', details=e.errors())

    try:
        enc = atualizar_encaminhamento_service(enc, dados.model_dump(exclude_none=True))
    except IntegrityError:
        return error('Não foi possível atualizar encaminhamento.', 409, 'CONFLICT')

    usuario_id = int(get_jwt_identity())
    registrar_atividade_encaminhamento(usuario_id, 'update', enc)
    return success('Encaminhamento atualizado com sucesso.', data={'item': serializar_encaminhamento(enc)})


# ---------------------------------------------------------------------------
# Registro de retorno
# ---------------------------------------------------------------------------

@encaminhamentos_bp.post('/<int:enc_id>/retorno')
@jwt_required_any
def registrar_retorno(enc_id: int):
    """Registra o retorno recebido para um encaminhamento."""
    enc = buscar_encaminhamento_service(enc_id)

    # Validação multi-tenant: O aluno associado deve pertencer à mesma unidade do usuário logado (a menos que seja admin)
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id')
    if perfil != 'administrador' and enc.aluno and enc.aluno.unidade_id != unidade_id:
        return error('Acesso não autorizado a este encaminhamento.', 403, 'FORBIDDEN')

    payload = request.get_json(silent=True) or {}
    try:
        dados = EncaminhamentoRetornoSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos.', 400, 'VALIDATION_ERROR', details=e.errors())

    enc = registrar_retorno_service(enc, dados.model_dump(exclude_none=True))

    usuario_id = int(get_jwt_identity())
    registrar_atividade_encaminhamento(usuario_id, 'retorno', enc)
    return success('Retorno registrado com sucesso.', data={'item': serializar_encaminhamento(enc)})
