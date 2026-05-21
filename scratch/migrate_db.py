import psycopg2
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = ROOT_DIR / ".env"

def load_dotenv(dotenv_path: Path) -> None:
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

load_dotenv(DEFAULT_ENV_FILE)

conn = psycopg2.connect(
    host=os.getenv("PGHOST", "localhost"),
    port=int(os.getenv("PGPORT", "5432")),
    user=os.getenv("PGUSER", "postgres"),
    password=os.getenv("PGPASSWORD", ""),
    dbname=os.getenv("PGDATABASE", "saadi_db"),
)

try:
    with conn.cursor() as cur:
        print("Running database migrations...")
        cur.execute("ALTER TABLE triagens ADD COLUMN IF NOT EXISTS queixa_principal TEXT;")
        cur.execute("ALTER TABLE triagens ADD COLUMN IF NOT EXISTS avaliacoes_json JSONB;")
        conn.commit()
        print("Migrations completed successfully!")
except Exception as e:
    print(f"Error executing migrations: {e}")
    conn.rollback()
finally:
    conn.close()
