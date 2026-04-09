from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = ROOT_DIR / '.env'


def load_dotenv(dotenv_path: Path = DEFAULT_ENV_FILE) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue

        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


class Config:
    load_dotenv()

    SECRET_KEY = os.getenv('SECRET_KEY', 'saadi-dev-secret')
    SQLALCHEMY_DATABASE_URI = (
        os.getenv('DATABASE_URL')
        or f"postgresql+psycopg2://{os.getenv('PGUSER', 'postgres')}:{os.getenv('PGPASSWORD', '')}"
        f"@{os.getenv('PGHOST', 'localhost')}:{os.getenv('PGPORT', '5432')}/{os.getenv('PGDATABASE', 'saadi_db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False
