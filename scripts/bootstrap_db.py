"""Bootstrap de banco PostgreSQL para o projeto SAADI.

O script:
1. Le variaveis de ambiente (ou arquivo .env).
2. Cria o banco de dados alvo, se nao existir.
3. Aplica db/schema.sql.
4. Aplica db/seed.sql.

Uso:
    python scripts/bootstrap_db.py
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = ROOT_DIR / ".env"


def load_dotenv(dotenv_path: Path) -> None:
    """Carrega um arquivo .env simples sem dependencia externa."""
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_config() -> dict[str, str | int]:
    load_dotenv(DEFAULT_ENV_FILE)

    return {
        "host": os.getenv("PGHOST", "localhost"),
        "port": int(os.getenv("PGPORT", "5432")),
        "user": os.getenv("PGUSER", "postgres"),
        "password": os.getenv("PGPASSWORD", ""),
        "database": os.getenv("PGDATABASE", "saadi_db"),
        "maintenance_db": os.getenv("PGMAINTENANCE_DB", "postgres"),
        "schema_file": os.getenv("SAADI_SCHEMA_FILE", str(ROOT_DIR / "db" / "schema.sql")),
        "seed_file": os.getenv("SAADI_SEED_FILE", str(ROOT_DIR / "db" / "seed.sql")),
    }


def connect_db(host: str, port: int, user: str, password: str, database: str):
    return psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=database,
    )


def ensure_database_exists(cfg: dict[str, str | int]) -> None:
    host = str(cfg["host"])
    port = int(cfg["port"])
    user = str(cfg["user"])
    password = str(cfg["password"])
    maintenance_db = str(cfg["maintenance_db"])
    database = str(cfg["database"])

    conn = connect_db(host, port, user, password, maintenance_db)
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
            exists = cur.fetchone() is not None

            if exists:
                print(f"[OK] Banco '{database}' ja existe.")
                return

            cur.execute(
                sql.SQL("CREATE DATABASE {} ENCODING 'UTF8' TEMPLATE template0").format(
                    sql.Identifier(database)
                )
            )
            print(f"[OK] Banco '{database}' criado com sucesso.")
    finally:
        conn.close()


def run_sql_file(conn, file_path: Path) -> None:
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo SQL nao encontrado: {file_path}")

    script = file_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(script)


def apply_schema_and_seed(cfg: dict[str, str | int]) -> None:
    host = str(cfg["host"])
    port = int(cfg["port"])
    user = str(cfg["user"])
    password = str(cfg["password"])
    database = str(cfg["database"])

    schema_file = Path(str(cfg["schema_file"]))
    seed_file = Path(str(cfg["seed_file"]))

    conn = connect_db(host, port, user, password, database)

    try:
        conn.autocommit = False

        print(f"[RUN] Aplicando schema: {schema_file}")
        run_sql_file(conn, schema_file)
        conn.commit()
        print("[OK] Schema aplicado.")

        print(f"[RUN] Aplicando seed: {seed_file}")
        run_sql_file(conn, seed_file)
        conn.commit()
        print("[OK] Seed aplicada.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_demo_users(cfg: dict[str, str | int]) -> None:
    host = str(cfg["host"])
    port = int(cfg["port"])
    user = str(cfg["user"])
    password = str(cfg["password"])
    database = str(cfg["database"])

    conn = connect_db(host, port, user, password, database)
    conn.autocommit = False

    demo_users = [
        {
            'nome': 'Administrador SAADI',
            'cpf': '111.111.111-11',
            'email': 'admin@saadi.local',
            'matricula': 'ADM001',
            'senha': 'Admin@12345!',
            'perfil': 'administrador',
            'departamento': 'administrativo',
        },
        {
            'nome': 'Secretaria SAADI',
            'cpf': '222.222.222-22',
            'email': 'secretaria@saadi.local',
            'matricula': 'SEC001',
            'senha': 'Secretaria@12345!',
            'perfil': 'secretaria',
            'departamento': 'secretaria',
        },
        {
            'nome': 'Psicopedagogo SAADI',
            'cpf': '333.333.333-33',
            'email': 'psicopedagogo@saadi.local',
            'matricula': 'PSI001',
            'senha': 'Psicopedagogo@12345!',
            'perfil': 'psicopedagogo',
            'departamento': 'psicopedagogia',
        },
    ]

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nome FROM perfis")
            perfis_por_nome = {nome: perfil_id for perfil_id, nome in cur.fetchall()}

            cur.execute(
                "SELECT id FROM unidades WHERE nome = %s AND sigla = %s",
                ('Escola Municipal Centro', 'EMC'),
            )
            unidade_row = cur.fetchone()

            if unidade_row is None:
                cur.execute(
                    """
                    INSERT INTO unidades (nome, sigla, cnpj, email, status)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    ('Escola Municipal Centro', 'EMC', '00.000.000/0001-00', 'contato@emc.saadi.local', 'ativa'),
                )
                unidade_id = cur.fetchone()[0]
            else:
                unidade_id = unidade_row[0]

            for demo in demo_users:
                cur.execute(
                    "SELECT 1 FROM usuarios WHERE email = %s",
                    (demo['email'],),
                )
                if cur.fetchone() is not None:
                    continue

                perfil_id = perfis_por_nome[demo['perfil']]
                senha_hash = generate_password_hash(demo['senha'])
                unidade_relacionada = None if demo['perfil'] == 'administrador' else unidade_id

                cur.execute(
                    """
                    INSERT INTO usuarios (
                        unidade_id, perfil_id, nome_completo, cpf, email,
                        matricula, senha_hash, departamento, status, enviar_email_boas_vindas
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        unidade_relacionada,
                        perfil_id,
                        demo['nome'],
                        demo['cpf'],
                        demo['email'],
                        demo['matricula'],
                        senha_hash,
                        demo['departamento'],
                        'ativo',
                        False,
                    ),
                )

        conn.commit()
        print('[OK] Usuarios de desenvolvimento garantidos.')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    cfg = get_config()

    if not cfg["password"]:
        raise ValueError(
            "PGPASSWORD nao definido. Configure no .env ou variavel de ambiente antes de rodar."
        )

    print("[INFO] Iniciando bootstrap do banco SAADI...")
    ensure_database_exists(cfg)
    apply_schema_and_seed(cfg)
    ensure_demo_users(cfg)
    print("[DONE] Banco pronto para uso.")


if __name__ == "__main__":
    main()
