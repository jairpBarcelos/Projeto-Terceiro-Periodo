from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from werkzeug.security import check_password_hash, generate_password_hash
from pydantic import ValidationError

from schemas.auth_schemas import LoginSchema, RegisterSchema

from backend.extensions import db
from backend.models import Perfil, TokenBlocklist, Usuario
from backend.responses import created, error, success
from backend.services.audit import registrar_atividade
from backend.services.auth_service import (
    PROFILE_REDIRECTS,
    autenticar_login,
    buscar_perfil,
    criar_tokens,
    registrar_login,
    registrar_logout,
    renovar_usuario_por_refresh,
    revogar_token_atual,
    serializar_usuario,
    senha_segura,
)


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')




@auth_bp.post('/login')
def login():
    payload = request.get_json(silent=True) or request.form
    try:
        dados = LoginSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos.', 400, 'VALIDATION_ERROR', details=e.errors())

    usuario = autenticar_login(dados.email, dados.senha)

    if usuario is None:
        return error('Credenciais invalidas.', 401, 'INVALID_CREDENTIALS')

    redirect_url = PROFILE_REDIRECTS.get(usuario.perfil.nome, '/index.html')
    tokens = criar_tokens(usuario, create_access_token=create_access_token, create_refresh_token=create_refresh_token)
    registrar_login(usuario)

    resp, status_code = success(
        message='Login realizado com sucesso.',
        data={
            'redirect_url': redirect_url,
            'user': serializar_usuario(usuario),
        },
    )
    
    set_access_cookies(resp, tokens['access_token'])
    set_refresh_cookies(resp, tokens['refresh_token'])
    return resp, status_code


@auth_bp.post('/logout')
@jwt_required(optional=True)
def logout():
    try:
        verify_jwt_in_request()
        revogar_token_atual(get_jwt)
        registrar_logout(get_jwt, get_jwt_identity)
    except Exception:
        pass
    resp, status_code = success('Logout realizado com sucesso.', data={'redirect_url': '/index.html'})
    unset_jwt_cookies(resp)
    return resp, status_code


@auth_bp.post('/refresh')
@jwt_required(refresh=True)
def refresh_token():
    usuario = renovar_usuario_por_refresh(int(get_jwt_identity()))

    if usuario is None:
        resp, status_code = error('Credenciais invalidas.', 401, 'INVALID_CREDENTIALS')
        unset_jwt_cookies(resp)
        return resp, status_code

    revogar_token_atual(get_jwt)
    db.session.commit()

    tokens = criar_tokens(usuario, create_access_token=create_access_token, create_refresh_token=create_refresh_token)
    resp, status_code = success(
        message='Token renovado com sucesso.',
        data={
            'user': serializar_usuario(usuario),
        },
    )
    set_access_cookies(resp, tokens['access_token'])
    return resp, status_code


@auth_bp.get('/me')
@jwt_required()
def me():
    claims = get_jwt()
    usuario = Usuario.query.get(int(claims['sub']))
    if not usuario:
        return error('Usuario nao encontrado.', 404, 'NOT_FOUND')
        
    return success(
        'Sessao validada com sucesso.',
        data={
            'authenticated': True,
            'user_id': usuario.id,
            'user_name': usuario.nome_completo,
            'email': usuario.email,
            'cpf': usuario.cpf,
            'perfil': usuario.perfil.nome,
            'unidade_id': usuario.unidade_id,
            'unidade_nome': usuario.unidade.nome if usuario.unidade else None,
            'redirect_url': PROFILE_REDIRECTS.get(usuario.perfil.nome, '/index.html'),
        },
    )


@auth_bp.put('/me')
@jwt_required()
def update_me():
    usuario_id = int(get_jwt_identity())
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return error('Usuario nao encontrado.', 404, 'NOT_FOUND')

    payload = request.get_json(silent=True) or {}
    
    if 'nome_completo' in payload:
        usuario.nome_completo = payload['nome_completo']
    
    if 'senha' in payload and payload['senha'].strip():
        usuario.senha_hash = senha_segura(payload['senha'])

    db.session.commit()
    registrar_atividade(usuario, 'Atualização de Perfil', 'Usuário', f'ID: {usuario.id}', 'Sucesso')

    return success('Perfil atualizado com sucesso.', data={'user': serializar_usuario(usuario)})


@auth_bp.post('/register')
def register():
    payload = request.get_json(silent=True) or {}
    try:
        dados = RegisterSchema(**payload)
    except ValidationError as e:
        return error('Dados inválidos.', 400, 'VALIDATION_ERROR', details=e.errors())

    perfil = buscar_perfil(dados.perfil_id or dados.perfil_nome or 'administrador')
    if perfil is None:
        return error('Perfil invalido.', 400, 'INVALID_PROFILE')

    if Usuario.query.filter(db.func.lower(Usuario.email) == dados.email.lower(), Usuario.deleted_at.is_(None)).first():
        return error('Email ja cadastrado.', 409, 'CONFLICT')

    usuario = Usuario(
        nome_completo=dados.nome,
        cpf=str(dados.cpf or dados.email.split('@')[0]).strip(),
        email=dados.email.lower(),
        matricula=str(dados.matricula or dados.email).strip(),
        senha_hash=senha_segura(dados.senha),
        perfil_id=perfil.id,
        unidade_id=dados.unidade_id,
        status=dados.status or 'ativo',
    )
    db.session.add(usuario)
    db.session.commit()

    return created('Usuario registrado com sucesso.', data={'user': serializar_usuario(usuario)})
