"""Rota para o dashboard geral do psicopedagogo."""
from __future__ import annotations

from flask import Blueprint
from flask_jwt_extended import get_jwt

from backend.responses import success
from backend.security import jwt_required_any
from backend.services.psicopedagogo_service import obter_dashboard_psicopedagogo_service


psicopedagogo_dashboard_bp = Blueprint('psicopedagogo_dashboard', __name__, url_prefix='/api/psicopedagogo')


@psicopedagogo_dashboard_bp.get('/dashboard')
@jwt_required_any
def obter_dashboard():
    """Retorna os indicadores consolidados para o painel principal do psicopedagogo."""
    claims = get_jwt()
    perfil = claims.get('perfil')
    
    # Se não for admin, filtra pela unidade do usuário
    unidade_id = claims.get('unidade_id') if perfil != 'administrador' else None

    dados = obter_dashboard_psicopedagogo_service(unidade_id)
    return success('Estatísticas do painel do psicopedagogo carregadas com sucesso.', data=dados)
