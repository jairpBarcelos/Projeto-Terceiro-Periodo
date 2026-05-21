"""Rotas para o módulo de Relatórios Técnicos e Pareceres."""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt, get_jwt_identity
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from schemas.relatorio_schemas import RelatorioCreateSchema, RelatorioUpdateSchema
from backend.responses import created, error, success
from backend.security import jwt_required_any
from backend.services.relatorios_service import (
    buscar_relatorio_service,
    criar_relatorio_service,
    listar_relatorios_service,
    obter_dashboard_relatorios_service,
    registrar_atividade_relatorio,
    serializar_relatorio,
)


relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/api/relatorios')


@relatorios_bp.get('/dashboard')
@jwt_required_any
def obter_dashboard():
    """Retorna métricas consolidadas dos relatórios técnicos."""
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    dados = obter_dashboard_relatorios_service(unidade_id)
    return success('Estatísticas de relatórios carregadas com sucesso.', data=dados)


@relatorios_bp.get('')
@jwt_required_any
def listar_relatorios():
    """Lista relatórios com filtros, paginação e controle multi-tenant."""
    status = request.args.get('status')
    q = (request.args.get('q') or '').strip()
    page = max(1, request.args.get('page', default=1, type=int))
    limit = min(max(1, request.args.get('limit', default=20, type=int)), 100)

    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    dados = listar_relatorios_service(
        autor_id=None,
        status=status,
        q=q,
        page=page,
        limit=limit,
        unidade_id=unidade_id,
    )
    return success('Relatórios e laudos técnicos carregados com sucesso.', data=dados)


@relatorios_bp.get('/<int:relatorio_id>')
@jwt_required_any
def obter_relatorio(relatorio_id: int):
    """Busca um relatório por ID, validando isolamento de escola (multi-tenant)."""
    claims = get_jwt()
    perfil = claims.get('perfil')
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    try:
        relatorio = buscar_relatorio_service(relatorio_id, unidade_id)
    except ValueError as exc:
        return error(str(exc), 403, 'FORBIDDEN')

    return success('Relatório técnico carregado com sucesso.', data={'item': serializar_relatorio(relatorio)})


@relatorios_bp.post('')
@jwt_required_any
def criar_relatorio():
    """Cadastra um novo relatório ou parecer técnico psicopedagógico."""
    payload = request.get_json(silent=True) or {}
    try:
        dados = RelatorioCreateSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos para relatório.', 400, 'VALIDATION_ERROR', details=e.errors())

    autor_id = int(get_jwt_identity())

    try:
        relatorio = criar_relatorio_service(dados.model_dump(exclude_none=True), autor_id)
    except ValueError as exc:
        return error(str(exc), 400, 'VALIDATION_ERROR')
    except IntegrityError:
        return error('Erro de integridade ao salvar relatório.', 409, 'CONFLICT')

    registrar_atividade_relatorio(autor_id, 'create', relatorio)
    return created('Relatório técnico emitido com sucesso.', data={'item': serializar_relatorio(relatorio)})
