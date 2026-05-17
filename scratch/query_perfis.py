import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import create_app
from backend.models import Perfil

app = create_app()
with app.app_context():
    perfis = Perfil.query.all()
    for p in perfis:
        print(f"ID: {p.id}, Nome: {p.nome}")
