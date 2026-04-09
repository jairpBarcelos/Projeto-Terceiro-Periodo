from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from sqlalchemy import text

from backend.config import Config
from backend.extensions import db
from backend.routes.auth import auth_bp


ROOT_DIR = Path(__file__).resolve().parents[1]


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    app.register_blueprint(auth_bp)

    @app.get('/')
    def home():
        return send_from_directory(ROOT_DIR, 'index.html')

    @app.get('/index.html')
    def login_page():
        return send_from_directory(ROOT_DIR, 'index.html')

    @app.get('/css/<path:filename>')
    def css_assets(filename: str):
        return send_from_directory(ROOT_DIR / 'css', filename)

    @app.get('/img/<path:filename>')
    def image_assets(filename: str):
        return send_from_directory(ROOT_DIR / 'img', filename)

    @app.get('/pages/<path:filename>')
    def page_assets(filename: str):
        return send_from_directory(ROOT_DIR / 'pages', filename)

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
