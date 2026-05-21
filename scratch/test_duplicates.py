import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import create_app
from backend.services.encaminhamentos_service import listar_encaminhamentos_service
from backend.models import Encaminhamento, Aluno, Usuario

app = create_app()

with app.app_context():
    # Let's inspect the results returned by listar_encaminhamentos_service
    res = listar_encaminhamentos_service(
        solicitante_id=None,
        tipo=None,
        status=None,
        q='',
        page=1,
        limit=100,
        unidade_id=4
    )
    print("RESULTS FOR UNIDADE 4:")
    print(f"Total: {res['total']}")
    for idx, item in enumerate(res['items']):
        print(f"{idx + 1}: ID={item['id']}, Aluno={item['aluno_nome']}, Tipo={item['tipo']}")

    res_all = listar_encaminhamentos_service(
        solicitante_id=None,
        tipo=None,
        status=None,
        q='',
        page=1,
        limit=100,
        unidade_id=None
    )
    print("\nRESULTS FOR ALL:")
    print(f"Total: {res_all['total']}")
    for idx, item in enumerate(res_all['items']):
        print(f"{idx + 1}: ID={item['id']}, Aluno={item['aluno_nome']}, Tipo={item['tipo']}")
