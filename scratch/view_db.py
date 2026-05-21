import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import create_app
from backend.models import Encaminhamento, Aluno, Usuario
from backend.extensions import db

app = create_app()

with app.app_context():
    all_encs = Encaminhamento.query.all()
    print("ALL ENCAMINHAMENTOS IN DB:")
    for enc in all_encs:
        print(f"ID={enc.id}, AlunoID={enc.aluno_id}, AlunoNome={enc.aluno.nome_completo if enc.aluno else 'None'}, SolicitanteID={enc.solicitante_id}, Status={enc.status}, CreatedAt={enc.created_at}")

    all_alunos = Aluno.query.all()
    print("\nALL ALUNOS IN DB:")
    for aluno in all_alunos:
        print(f"ID={aluno.id}, Nome={aluno.nome_completo}, UnidadeID={aluno.unidade_id}")
