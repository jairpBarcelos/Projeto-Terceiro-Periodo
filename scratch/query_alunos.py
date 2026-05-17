import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.extensions import db
from backend.models import Aluno, Unidade
from backend import create_app

app = create_app()

with app.app_context():
    alunos = Aluno.query.all()
    print("ALUNOS:")
    for a in alunos:
        print(f"- ID: {a.id}, Nome: {a.nome_completo}, Unidade_ID: {a.unidade_id}")
    
    unidades = Unidade.query.all()
    print("\nUNIDADES:")
    for u in unidades:
        print(f"- ID: {u.id}, Nome: {u.nome}")
