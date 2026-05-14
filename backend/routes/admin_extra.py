from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import IntegrityError

from backend.extensions import db
from backend.models import CategoriaNeurodiversidade
from backend.responses import created, error, success
from backend.security import jwt_required_admin
from backend.services.admin_panel_service import (
    atualizar_parametros_service,
    listar_alunos_service,
    obter_parametros_service,
    obter_relatorios_dashboard_service,
)
from backend.services.anos_letivos_service import (
    listar_anos_letivos_service,
    criar_ano_letivo_service,
    atualizar_ano_letivo_service,
    remover_ano_letivo_service
)
from backend.services.audit import registrar_atividade


admin_extra_bp = Blueprint('admin_extra', __name__, url_prefix='/api/admin')


@admin_extra_bp.get('/relatorios/dashboard')
@jwt_required_admin
def relatorios_dashboard():
    return success('Relatorios carregados com sucesso.', data=obter_relatorios_dashboard_service())


@admin_extra_bp.get('/parametros')
@jwt_required_admin
def parametros():
    return success('Parametros carregados com sucesso.', data=obter_parametros_service())


@admin_extra_bp.put('/parametros')
@jwt_required_admin
def atualizar_parametros():
    payload = request.get_json(silent=True) or {}
    return success('Parametros atualizados com sucesso.', data=atualizar_parametros_service(payload))


@admin_extra_bp.get('/alunos')
@jwt_required_admin
def alunos():
    page = max(1, request.args.get('page', default=1, type=int))
    limit = min(max(1, request.args.get('limit', default=20, type=int)), 100)
    q = (request.args.get('q') or '').strip()
    unidade_id = request.args.get('unidade_id', type=int)
    serie = request.args.get('serie')
    diagnostico = request.args.get('diagnostico')
    status = request.args.get('status')

    return success(
        'Alunos carregados com sucesso.',
        data=listar_alunos_service(
            page=page,
            limit=limit,
            q=q or None,
            unidade_id=unidade_id,
            serie=serie,
            diagnostico=diagnostico,
            status=status,
        ),
    )


# --- ROTAS DE ANOS LETIVOS ---

@admin_extra_bp.get('/anos-letivos')
@jwt_required_admin
def listar_anos_letivos():
    return success('Anos letivos carregados.', data=listar_anos_letivos_service())


@admin_extra_bp.post('/anos-letivos')
@jwt_required_admin
def criar_ano_letivo():
    payload = request.get_json(silent=True) or {}
    res = criar_ano_letivo_service(payload)
    if isinstance(res, tuple):  # Se for um erro (response, status)
        return res
    return success('Ano letivo criado com sucesso.', data=res)


@admin_extra_bp.put('/anos-letivos/<int:id>')
@jwt_required_admin
def atualizar_ano_letivo(id):
    payload = request.get_json(silent=True) or {}
    res = atualizar_ano_letivo_service(id, payload)
    if isinstance(res, tuple):
        return res
    return success('Ano letivo atualizado com sucesso.', data=res)


@admin_extra_bp.delete('/anos-letivos/<int:id>')
@jwt_required_admin
def remover_ano_letivo(id):
    remover_ano_letivo_service(id)
    return success('Ano letivo removido com sucesso.')


# --- ROTAS DE CATEGORIAS DE NEURODIVERSIDADE ---

@admin_extra_bp.get('/categorias')
@jwt_required_admin
def listar_categorias():
    """Lista todas as categorias de neurodiversidade."""
    categorias = CategoriaNeurodiversidade.query.order_by(CategoriaNeurodiversidade.nome.asc()).all()
    items = [
        {
            'id': c.id,
            'nome': c.nome,
            'descricao': c.descricao,
            'ativa': c.ativa,
            'created_at': c.created_at.isoformat() if c.created_at else None,
        }
        for c in categorias
    ]
    return success('Categorias carregadas com sucesso.', data={'items': items, 'total': len(items)})


@admin_extra_bp.post('/categorias')
@jwt_required_admin
def criar_categoria():
    """Cria uma nova categoria de neurodiversidade."""
    payload = request.get_json(silent=True) or {}
    nome = (payload.get('nome') or '').strip()
    if not nome:
        return error('O nome da categoria é obrigatório.', 400, 'VALIDATION_ERROR')

    categoria = CategoriaNeurodiversidade(
        nome=nome,
        descricao=(payload.get('descricao') or '').strip() or None,
        ativa=payload.get('ativa', True),
    )

    try:
        db.session.add(categoria)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error('Já existe uma categoria com esse nome.', 409, 'CONFLICT')

    registrar_atividade(
        int(get_jwt_identity()), 'create', 'categoria_neurodiversidade', categoria.id,
        detalhes={'nome': categoria.nome},
        ip_origem=request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()

    return created('Categoria criada com sucesso.', data={
        'item': {'id': categoria.id, 'nome': categoria.nome, 'descricao': categoria.descricao, 'ativa': categoria.ativa}
    })


@admin_extra_bp.put('/categorias/<int:categoria_id>')
@jwt_required_admin
def atualizar_categoria(categoria_id: int):
    """Atualiza uma categoria de neurodiversidade existente."""
    categoria = CategoriaNeurodiversidade.query.get_or_404(categoria_id)
    payload = request.get_json(silent=True) or {}

    nome = (payload.get('nome') or '').strip()
    if nome:
        categoria.nome = nome

    if 'descricao' in payload:
        categoria.descricao = (payload['descricao'] or '').strip() or None

    if 'ativa' in payload:
        categoria.ativa = bool(payload['ativa'])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error('Já existe uma categoria com esse nome.', 409, 'CONFLICT')

    registrar_atividade(
        int(get_jwt_identity()), 'update', 'categoria_neurodiversidade', categoria.id,
        detalhes={'nome': categoria.nome, 'ativa': categoria.ativa},
        ip_origem=request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()

    return success('Categoria atualizada com sucesso.', data={
        'item': {'id': categoria.id, 'nome': categoria.nome, 'descricao': categoria.descricao, 'ativa': categoria.ativa}
    })


@admin_extra_bp.delete('/categorias/<int:categoria_id>')
@jwt_required_admin
def deletar_categoria(categoria_id: int):
    """Remove uma categoria de neurodiversidade."""
    categoria = CategoriaNeurodiversidade.query.get_or_404(categoria_id)

    registrar_atividade(
        int(get_jwt_identity()), 'delete', 'categoria_neurodiversidade', categoria.id,
        detalhes={'nome': categoria.nome},
        ip_origem=request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent=request.headers.get('User-Agent'),
    )

    db.session.delete(categoria)
    db.session.commit()

    return success('Categoria removida com sucesso.')

