"""Rotas CRUD para gerenciamento de Alunos."""
from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

from schemas.aluno_schemas import AlunoCreateSchema, AlunoUpdateSchema

from backend.responses import created, error, success
from backend.security import jwt_required_any
from backend.services.alunos_service import (
    atualizar_aluno_service,
    buscar_aluno_service,
    criar_aluno_service,
    deletar_aluno_service,
    listar_alunos_service,
    registrar_atividade_aluno,
    serializar_aluno,
)


alunos_bp = Blueprint('alunos', __name__, url_prefix='/api/alunos')


@alunos_bp.get('')
@jwt_required_any
def listar_alunos():
    """Lista alunos com paginação e filtros opcionais."""
    unidade_id = request.args.get('unidade_id', default=None, type=int)
    status = request.args.get('status')
    q = (request.args.get('q') or '').strip()
    page = max(1, request.args.get('page', default=1, type=int))
    limit = min(max(1, request.args.get('limit', default=20, type=int)), 100)
    incluir_excluidos = request.args.get('incluir_excluidos', 'false').lower() == 'true'

    return success(
        'Alunos carregados com sucesso.',
        data=listar_alunos_service(unidade_id, status, q, page, limit, incluir_excluidos),
    )


@alunos_bp.get('/<int:aluno_id>')
@jwt_required_any
def buscar_aluno(aluno_id: int):
    """Retorna os dados completos de um aluno por ID."""
    aluno = buscar_aluno_service(aluno_id)
    return success('Aluno carregado com sucesso.', data={'item': serializar_aluno(aluno)})


@alunos_bp.post('')
@jwt_required_any
def criar_aluno():
    """Cadastra um novo aluno no sistema."""
    payload = request.get_json(silent=True) or {}
    try:
        dados = AlunoCreateSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos.', 400, 'VALIDATION_ERROR', details=e.errors())

    try:
        aluno = criar_aluno_service(dados.model_dump(exclude_none=True))
    except IntegrityError:
        return error('Não foi possível criar aluno. Verifique CPF duplicado.', 409, 'CONFLICT')
    except ValueError as exc:
        return error(str(exc), 400, 'VALIDATION_ERROR')

    registrar_atividade_aluno(int(get_jwt_identity()), 'create', aluno)
    return created('Aluno cadastrado com sucesso.', data={'item': serializar_aluno(aluno)})


@alunos_bp.put('/<int:aluno_id>')
@jwt_required_any
def atualizar_aluno(aluno_id: int):
    """Atualiza os dados de um aluno existente."""
    aluno = buscar_aluno_service(aluno_id)
    payload = request.get_json(silent=True) or {}
    try:
        dados = AlunoUpdateSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos.', 400, 'VALIDATION_ERROR', details=e.errors())

    try:
        aluno = atualizar_aluno_service(aluno, dados.model_dump(exclude_none=True))
    except IntegrityError:
        return error('Não foi possível atualizar aluno. Verifique conflitos de dados.', 409, 'CONFLICT')

    registrar_atividade_aluno(int(get_jwt_identity()), 'update', aluno)
    return success('Aluno atualizado com sucesso.', data={'item': serializar_aluno(aluno)})


@alunos_bp.delete('/<int:aluno_id>')
@jwt_required_any
def deletar_aluno(aluno_id: int):
    """Remove um aluno (soft delete)."""
    aluno = buscar_aluno_service(aluno_id)
    aluno = deletar_aluno_service(aluno)
    registrar_atividade_aluno(int(get_jwt_identity()), 'delete', aluno)
    return success('Aluno removido com sucesso (soft delete).')
