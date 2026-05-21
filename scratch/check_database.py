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
        print("=== ALUNOS ===")
        cur.execute("SELECT id, nome_completo, cpf, unidade_id FROM alunos;")
        for row in cur.fetchall():
            print(row)
            
        print("\n=== USUARIOS ===")
        cur.execute("SELECT id, nome_completo, email, unidade_id, perfil_id FROM usuarios;")
        for row in cur.fetchall():
            print(row)
            
        print("\n=== ENCAMINHAMENTOS ===")
        cur.execute("SELECT id, aluno_id, solicitante_id, destino, tipo, status FROM encaminhamentos;")
        for row in cur.fetchall():
            print(row)
            
        print("\n=== JOIN QUERY ===")
        cur.execute("""
            SELECT e.id, a.nome_completo, u.nome_completo
            FROM encaminhamentos e
            JOIN alunos a ON e.aluno_id = a.id
            JOIN usuarios u ON e.solicitante_id = u.id;
        """)
        for row in cur.fetchall():
            print(row)
finally:
    conn.close()
