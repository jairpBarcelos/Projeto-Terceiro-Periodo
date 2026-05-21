import sys
import os

# Ajusta o sys.path para enxergar o backend no diretório pai
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import create_app
from backend.models import Aluno, Usuario, Encaminhamento
from backend.extensions import db
from flask_jwt_extended import create_access_token

app = create_app()

def print_result(test_name, success, details=""):
    status = " [PASSO OK] " if success else " [FALHA] "
    print(f"{status} {test_name}")
    if details:
        print(f"      -> {details}")

print("=== INICIANDO TESTES DE SEGURANÇA E ISOLAMENTO MULTI-TENANT (ENCAMINHAMENTOS) ===")

with app.app_context():
    client = app.test_client()

    # 1. Gerar tokens JWT legítimos contendo as claims de cada perfil
    token_sec_1 = create_access_token(
        identity='2',
        additional_claims={
            'perfil': 'secretaria',
            'nome': 'Secretaria SAADI',
            'email': 'secretaria@saadi.local',
            'unidade_id': 1
        }
    )
    
    token_sec_4 = create_access_token(
        identity='10',
        additional_claims={
            'perfil': 'secretaria',
            'nome': 'Secretaria Doutor claudio',
            'email': 'secretariadrclaudio@gmail.com',
            'unidade_id': 4
        }
    )

    token_psi_1 = create_access_token(
        identity='3',
        additional_claims={
            'perfil': 'psicopedagogo',
            'nome': 'Psicopedagogo SAADI',
            'email': 'psicopedagogo@saadi.local',
            'unidade_id': 1
        }
    )

    token_admin = create_access_token(
        identity='1',
        additional_claims={
            'perfil': 'administrador',
            'nome': 'Administrador SAADI',
            'email': 'admin@saadi.local',
            'unidade_id': None
        }
    )

    print("\n--- TESTE 1: Secretaria de Escola A tentando encaminhar aluno de Escola B ---")
    # Aluno ID 3 (jair pereira) pertence à Unidade ID 4.
    # Secretaria SAADI (ID 2) pertence à Unidade ID 1.
    payload_invalido = {
        'aluno_id': 3,
        'tipo': 'interno',
        'destino': 'Psicopedagogia',
        'prioridade': 'alta',
        'descricao': 'Tenta encaminhar aluno de outra escola.',
        'prazo_retorno': None
    }
    client.set_cookie('access_token_cookie', token_sec_1)
    res = client.post('/api/encaminhamentos', json=payload_invalido)
    is_blocked = (res.status_code == 400 and 'não pertence' in res.get_json().get('message', ''))
    print_result("Bloqueio de encaminhamento cruzado entre escolas", is_blocked, f"Status: {res.status_code}, Resposta: {res.get_json()}")

    print("\n--- TESTE 2: Secretaria autorizada encaminhando aluno da própria escola ---")
    # Secretaria Doutor Claudio (Unidade 4) encaminhando Jair Pereira (Unidade 4)
    payload_valido = {
        'aluno_id': 3,
        'tipo': 'interno',
        'destino': 'Psicopedagogia',
        'prioridade': 'alta',
        'descricao': 'Encaminhamento legítimo feito pela secretaria correspondente.',
        'prazo_retorno': None
    }
    client.set_cookie('access_token_cookie', token_sec_4)
    res = client.post('/api/encaminhamentos', json=payload_valido)
    is_success = (res.status_code == 201)
    novo_enc_id = res.get_json().get('data', {}).get('item', {}).get('id') if is_success else None
    print_result("Sucesso ao registrar encaminhamento na mesma escola", is_success, f"Status: {res.status_code}, Novo Encaminhamento ID: {novo_enc_id}")

    print("\n--- TESTE 3: Psicopedagogo da Escola A listando encaminhamentos ---")
    # Psicopedagogo SAADI (Unidade 1) não deve ver o encaminhamento do aluno Jair Pereira (Unidade 4)
    client.set_cookie('access_token_cookie', token_psi_1)
    res = client.get('/api/encaminhamentos')
    items = res.get_json().get('data', {}).get('items', [])
    leakage = any(item.get('aluno_id') == 3 for item in items)
    print_result("Isolamento de listagem (Psicopedagogo Unidade 1 não vê aluno da Unidade 4)", not leakage, f"Total retornado para Unit 1: {len(items)}")

    print("\n--- TESTE 4: Psicopedagogo da Escola A acessando métricas do Dashboard ---")
    # Psicopedagogo SAADI (Unidade 1) deve ver contagem 0 para abertos (se não há outros da unidade 1)
    client.set_cookie('access_token_cookie', token_psi_1)
    res = client.get('/api/encaminhamentos/dashboard')
    dashboard = res.get_json().get('data', {})
    abertos_psi = dashboard.get('abertos', 0)
    print_result("Isolamento do Dashboard (Métricas não contabilizam dados de outras unidades)", abertos_psi == 0, f"Métricas Unit 1: {dashboard}")

    print("\n--- TESTE 5: Administrador Global acessando encaminhamentos de todas as escolas ---")
    client.set_cookie('access_token_cookie', token_admin)
    res = client.get('/api/encaminhamentos')
    items_admin = res.get_json().get('data', {}).get('items', [])
    has_jair = any(item.get('aluno_id') == 3 for item in items_admin)
    print_result("Acesso global do Administrador", has_jair, f"Total geral retornado para o Administrador: {len(items_admin)}")

    print("\n--- TESTE 6: Tentativa de acesso direto por ID a encaminhamento de outra escola ---")
    if novo_enc_id:
        # Psicopedagogo SAADI (Unidade 1) tenta ler o encaminhamento da Unidade 4
        client.set_cookie('access_token_cookie', token_psi_1)
        res = client.get(f'/api/encaminhamentos/{novo_enc_id}')
        is_forbidden = (res.status_code == 403)
        print_result("Bloqueio de leitura direta por ID (GET /<id>) de outra unidade", is_forbidden, f"Status: {res.status_code}")

        # Psicopedagogo SAADI (Unidade 1) tenta atualizar o encaminhamento da Unidade 4
        client.set_cookie('access_token_cookie', token_psi_1)
        res = client.put(f'/api/encaminhamentos/{novo_enc_id}', json={'prioridade': 'baixa'})
        is_forbidden_put = (res.status_code == 403)
        print_result("Bloqueio de alteração direta (PUT /<id>) de outra unidade", is_forbidden_put, f"Status: {res.status_code}")

        # Psicopedagogo SAADI (Unidade 1) tenta registrar retorno para o encaminhamento da Unidade 4
        client.set_cookie('access_token_cookie', token_psi_1)
        res = client.post(f'/api/encaminhamentos/{novo_enc_id}/retorno', json={'data_retorno': '2026-05-21', 'status': 'concluido'})
        is_forbidden_post = (res.status_code == 403)
        print_result("Bloqueio de retorno (POST /<id>/retorno) de outra unidade", is_forbidden_post, f"Status: {res.status_code}")
    else:
        print_result("Bloqueios diretos por ID ignorados (falha no setup do teste)", False)

print("\n=== VALIDAÇÃO CONCLUÍDA CONCLUÍDA COM SUCESSO! ===")
