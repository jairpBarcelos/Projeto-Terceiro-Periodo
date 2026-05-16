from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
from sqlalchemy import inspect, text

from backend.extensions import db, jwt, migrate
from backend.models import TokenBlocklist  # noqa: F401 - garante registro no migrate.
from backend.responses import error
from backend.routes.admin_unidades import admin_unidades_bp
from backend.routes.admin_usuarios import admin_usuarios_bp
from backend.routes.admin_dashboard import admin_dashboard_bp
from backend.routes.admin_extra import admin_extra_bp
from backend.config import Config
from backend.routes.auth import auth_bp
from backend.routes.alunos import alunos_bp
from backend.routes.encaminhamentos import encaminhamentos_bp


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / 'frontend'


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r'/api/*': {'origins': app.config['CORS_ORIGINS']}}, supports_credentials=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_unidades_bp)
    app.register_blueprint(admin_usuarios_bp)
    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(admin_extra_bp)
    app.register_blueprint(alunos_bp)
    app.register_blueprint(encaminhamentos_bp)

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    with app.app_context():
        db.create_all()

    @jwt.token_in_blocklist_loader
    def verificar_token_revogado(_jwt_header: dict, jwt_payload: dict) -> bool:
        jti = jwt_payload.get('jti')
        if 'token_blocklist' not in inspect(db.engine).get_table_names():
            return False
        return TokenBlocklist.query.filter_by(jti=jti).first() is not None

    @jwt.revoked_token_loader
    def token_revogado_callback(_jwt_header: dict, _jwt_payload: dict):
        return jsonify(message='Token revogado.'), 401

    @jwt.unauthorized_loader
    def jwt_ausente_callback(message: str):
        return jsonify(message=message), 401

    @jwt.invalid_token_loader
    def jwt_invalido_callback(message: str):
        return error(message=message, status_code=422, code='INVALID_TOKEN')

    @jwt.expired_token_loader
    def jwt_expirado_callback(_jwt_header: dict, _jwt_payload: dict):
        return error(message='Token expirado.', status_code=401, code='TOKEN_EXPIRED')

    @app.errorhandler(HTTPException)
    def tratar_http_exception(erro: HTTPException):
        return error(
            message=erro.description or 'Erro na requisicao.',
            status_code=erro.code or 500,
            code=erro.name.upper().replace(' ', '_'),
        )

    @app.errorhandler(Exception)
    def tratar_excecao_generica(erro: Exception):
        app.logger.exception('Erro nao tratado: %s', erro)
        return error(message='Erro interno do servidor.', status_code=500, code='INTERNAL_SERVER_ERROR')

    @app.get('/')
    def home():
        return send_from_directory(FRONTEND_DIR, 'index.html')

    @app.get('/index.html')
    def login_page():
        return send_from_directory(FRONTEND_DIR, 'index.html')

    @app.get('/favicon.ico')
    def favicon():
        return send_from_directory(FRONTEND_DIR / 'assets', 'favicon.ico')

    @app.get('/css/<path:filename>')
    def css_assets(filename: str):
        return send_from_directory(FRONTEND_DIR / 'css', filename)

    @app.get('/img/<path:filename>')
    def image_assets(filename: str):
        return send_from_directory(FRONTEND_DIR / 'assets', filename)

    @app.get('/scripts/<path:filename>')
    def script_assets(filename: str):
        return send_from_directory(FRONTEND_DIR / 'js', filename)

    @app.get('/pages/<path:filename>')
    def page_assets(filename: str):
        return send_from_directory(FRONTEND_DIR / 'pages', filename)

    @app.get('/health')
    def health_check():
        with db.engine.connect() as connection:
            result = connection.execute(text('SELECT current_database() AS database, current_user AS user, version() AS version'))
            row = result.mappings().one()

        return jsonify(
            status='ok',
            database=row['database'],
            user=row['user'],
            version=row['version'],
        )

    return app
