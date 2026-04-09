from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash

from backend.extensions import db
from backend.models import Usuario


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

PROFILE_REDIRECTS = {
    'administrador': '/pages/menus/administrador/menuAdministrador.html',
    'secretaria': '/pages/menus/secretaria/menuSecretariaEscolar.html',
    'psicopedagogo': '/pages/menus/psicopedagogo/menuPsicopedagogo.html',
    'professor': '/pages/menus/secretaria/menuSecretariaEscolar.html',
    'diretor': '/pages/menus/administrador/menuAdministrador.html',
}


@auth_bp.post('/login')
def login():
    payload = request.get_json(silent=True) or request.form
    email = (payload.get('email') or '').strip().lower()
    senha = payload.get('senha') or ''

    if not email or not senha:
        return jsonify(message='Informe email e senha.'), 400

    usuario = (
        Usuario.query
        .join(Usuario.perfil)
        .filter(db.func.lower(Usuario.email) == email, Usuario.deleted_at.is_(None))
        .first()
    )

    if usuario is None or usuario.status != 'ativo':
        return jsonify(message='Credenciais invalidas.'), 401

    if not check_password_hash(usuario.senha_hash, senha):
        return jsonify(message='Credenciais invalidas.'), 401

    usuario.ultimo_login_em = datetime.now(timezone.utc)
    db.session.commit()

    redirect_url = PROFILE_REDIRECTS.get(usuario.perfil.nome, '/index.html')
    session['user_id'] = usuario.id
    session['user_name'] = usuario.nome_completo
    session['profile_name'] = usuario.perfil.nome
    session['redirect_url'] = redirect_url

    return jsonify(
        message='Login realizado com sucesso.',
        redirect_url=redirect_url,
        user={
            'id': usuario.id,
            'nome': usuario.nome_completo,
            'email': usuario.email,
            'perfil': usuario.perfil.nome,
            'unidade_id': usuario.unidade_id,
        },
    )


@auth_bp.post('/logout')
def logout():
    session.clear()
    return jsonify(message='Logout realizado com sucesso.', redirect_url='/index.html')


@auth_bp.get('/me')
def me():
    if 'user_id' not in session:
        return jsonify(authenticated=False), 401

    return jsonify(
        authenticated=True,
        user_id=session.get('user_id'),
        user_name=session.get('user_name'),
        profile_name=session.get('profile_name'),
        redirect_url=session.get('redirect_url'),
    )
