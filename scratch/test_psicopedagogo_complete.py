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

print("=== INICIANDO SUÍTE DE TESTES INTEGRADOS DO PSICOPEDAGOGO ===")

with app.app_context():
    client = app.test_client()

    # 1. Gerar tokens JWT legítimos contendo as claims de cada perfil
    # Psicopedagogo Escola A (Unidade 1)
    token_psi_school_a = create_access_token(
        identity='3',
        additional_claims={
            'perfil': 'psicopedagogo',
            'nome': 'Psicopedagogo Escola A',
            'email': 'psicopedagogo_a@saadi.local',
            'unidade_id': 1
        }
    )

    # Psicopedagogo Escola B (Unidade 4)
    token_psi_school_b = create_access_token(
        identity='4',
        additional_claims={
            'perfil': 'psicopedagogo',
            'nome': 'Psicopedagogo Escola B',
            'email': 'psicopedagogo_b@saadi.local',
            'unidade_id': 4
        }
    )

    # Aluno ID 2 (gilvanio da silva fernandes) - Unidade 1
    # Aluno ID 3 (Jair Pereira) - Unidade 4

    print("\n--- SEÇÃO A: TESTES DE TRIAGENS E AVALIAÇÕES ---")
    
    # 1. Criar triagem legítima
    client.set_cookie('access_token_cookie', token_psi_school_a)
    payload_triagem_ok = {
        'aluno_id': 2,
        'data_registro': '2026-05-21',
        'tipo_registro': 'triagem',
        'descricao': 'Primeiro atendimento técnico psicopedagógico.',
        'evolucao': 'Estudante receptivo às estratégias de integração.',
        'observacoes': 'Avaliar necessidade de encaminhamento em fonoaudiologia.'
    }
    res = client.post('/api/triagens', json=payload_triagem_ok)
    is_success = (res.status_code == 201)
    triagem_id = res.get_json().get('data', {}).get('item', {}).get('id') if is_success else None
    print_result("Sucesso ao registrar nova Triagem (mesma unidade)", is_success, f"Status: {res.status_code}, Triagem ID: {triagem_id}")

    # 2. Bloqueio de triagem para aluno de outra unidade
    payload_triagem_block = {
        'aluno_id': 3,  # Unidade 4, mas estamos com token de Unidade 1
        'data_registro': '2026-05-21',
        'tipo_registro': 'atendimento',
        'descricao': 'Tentativa de invadir histórico escolar.'
    }
    res = client.post('/api/triagens', json=payload_triagem_block)
    is_blocked = (res.status_code == 400 and 'não pertence' in res.get_json().get('message', ''))
    print_result("Bloqueio de Triagem multi-tenant cruzada", is_blocked, f"Status: {res.status_code}")

    # 3. Listagem de triagens (deve listar apenas a da Unidade 1)
    res = client.get('/api/triagens')
    items = res.get_json().get('data', {}).get('items', [])
    leakage = any(item.get('aluno_id') == 3 for item in items)
    print_result("Isolamento de listagem de Triagens", not leakage, f"Total retornado para Escola A: {len(items)}")


    print("\n--- SEÇÃO B: TESTES DE PLANOS DE ACOMPANHAMENTO ---")

    # 1. Criar plano de acompanhamento legítimo
    payload_plano_ok = {
        'aluno_id': 2,
        'titulo': 'Plano Individualizado de Apoio Escolar',
        'objetivo_geral': 'Desenvolver autonomia no ambiente acadêmico.',
        'estrategias': 'Linguagem simplificada e auxílio visual.',
        'periodicidade': 'Semanal',
        'data_inicio': '2026-05-21',
        'data_fim_prevista': '2026-12-18'
    }
    res = client.post('/api/planos', json=payload_plano_ok)
    is_success = (res.status_code == 201)
    plano_id = res.get_json().get('data', {}).get('item', {}).get('id') if is_success else None
    print_result("Sucesso ao registrar novo Plano (mesma unidade)", is_success, f"Status: {res.status_code}, Plano ID: {plano_id}")

    # 2. Bloqueio de plano para aluno de outra unidade
    payload_plano_block = {
        'aluno_id': 3,
        'titulo': 'Tentativa invasão',
        'data_inicio': '2026-05-21'
    }
    res = client.post('/api/planos', json=payload_plano_block)
    is_blocked = (res.status_code == 400 and 'não pertence' in res.get_json().get('message', ''))
    print_result("Bloqueio de Plano multi-tenant cruzado", is_blocked, f"Status: {res.status_code}")

    # 3. Listagem de planos
    res = client.get('/api/planos')
    items = res.get_json().get('data', {}).get('items', [])
    leakage = any(item.get('aluno_id') == 3 for item in items)
    print_result("Isolamento de listagem de Planos", not leakage, f"Total retornado para Escola A: {len(items)}")


    print("\n--- SEÇÃO C: TESTES DE RELATÓRIOS TÉCNICOS ---")

    # 1. Criar laudo/relatório legítimo
    payload_relatorio_ok = {
        'aluno_id': 2,
        'tipo': 'parecer',
        'titulo': 'Parecer Técnico Sintetizado',
        'conteudo': 'Relatório gerado a partir de observação clínica.',
        'status': 'emitido',
        'ano_referencia': 2026,
        'periodo_inicio': '2026-05-01',
        'periodo_fim': '2026-05-21'
    }
    res = client.post('/api/relatorios', json=payload_relatorio_ok)
    is_success = (res.status_code == 201)
    relatorio_id = res.get_json().get('data', {}).get('item', {}).get('id') if is_success else None
    print_result("Sucesso ao criar Relatório Técnico (mesma unidade)", is_success, f"Status: {res.status_code}, Relatório ID: {relatorio_id}")

    # 2. Bloqueio de relatório de outra unidade
    payload_relatorio_block = {
        'aluno_id': 3,
        'tipo': 'laudo',
        'titulo': 'Bloqueado',
        'status': 'rascunho'
    }
    res = client.post('/api/relatorios', json=payload_relatorio_block)
    is_blocked = (res.status_code == 400 and 'não pertence' in res.get_json().get('message', ''))
    print_result("Bloqueio de Relatório multi-tenant cruzado", is_blocked, f"Status: {res.status_code}")

    # 3. Listagem de relatórios
    res = client.get('/api/relatorios')
    items = res.get_json().get('data', {}).get('items', [])
    leakage = any(item.get('aluno_id') == 3 for item in items)
    print_result("Isolamento de listagem de Relatórios", not leakage, f"Total retornado para Escola A: {len(items)}")


    print("\n--- SEÇÃO D: TESTES DO PAINEL / DASHBOARD CENTRAL DO PSICOPEDAGOGO ---")
    
    # Obter dados gerais do painel
    res = client.get('/api/psicopedagogo/dashboard')
    is_success = (res.status_code == 200)
    data = res.get_json().get('data', {}) if is_success else {}
    
    print_result("Dashboard Geral obtido com sucesso", is_success, f"Status: {res.status_code}")
    print(f"      -> Atendimentos Hoje: {data.get('atendimentos_hoje', 0)}")
    print(f"      -> Casos Acompanhamento: {data.get('casos_acompanhamento', 0)}")
    print(f"      -> Planos Ativos: {data.get('planos_ativos', 0)}")
    print(f"      -> Triagens Pendentes: {data.get('triagens_pendentes', 0)}")


    print("\n--- SEÇÃO E: FLUXO DE RETORNO DE ENCAMINHAMENTO ---")
    
    # Criar um encaminhamento legítimo para Escola A para podermos aplicar retorno
    payload_enc = {
        'aluno_id': 2,
        'tipo': 'externo',
        'destino': 'Neuropediatria',
        'prioridade': 'alta',
        'descricao': 'Avaliação de TDAH e orientação familiar.',
        'prazo_retorno': '2026-06-30'
    }
    
    # Criar via secretaria Escola A
    token_sec_school_a = create_access_token(
        identity='2',
        additional_claims={
            'perfil': 'secretaria',
            'nome': 'Secretaria Unidade 1',
            'email': 'sec_a@saadi.local',
            'unidade_id': 1
        }
    )
    client.set_cookie('access_token_cookie', token_sec_school_a)
    res = client.post('/api/encaminhamentos', json=payload_enc)
    enc_id = res.get_json().get('data', {}).get('item', {}).get('id') if res.status_code == 201 else None
    
    if enc_id:
        print_result("Encaminhamento para teste de retorno criado", True, f"Encaminhamento ID: {enc_id}")
        
        # 1. Registrar retorno legítimo (Psicopedagogo Escola A na Unidade 1)
        client.set_cookie('access_token_cookie', token_psi_school_a)
        payload_retorno = {
            'data_retorno': '2026-05-21',
            'observacao_retorno': 'Aluno avaliado pela neuropediatra. Iniciado uso de medicação e recomendada intervenção focada.',
            'status': 'concluido'
        }
        res = client.post(f'/api/encaminhamentos/{enc_id}/retorno', json=payload_retorno)
        is_success = (res.status_code == 200)
        ret_status = res.get_json().get('data', {}).get('item', {}).get('status') if is_success else None
        print_result("Registro de retorno de encaminhamento", is_success, f"Status HTTP: {res.status_code}, Status Final: {ret_status}")
        
        # 2. Bloqueio de retorno para psicopedagogo de outra unidade
        client.set_cookie('access_token_cookie', token_psi_school_b)
        res = client.post(f'/api/encaminhamentos/{enc_id}/retorno', json=payload_retorno)
        is_blocked = (res.status_code == 403)
        print_result("Bloqueio de retorno feito por outro tenant", is_blocked, f"Status: {res.status_code}")
    else:
        print_result("Falha ao configurar encaminhamento para teste de retorno", False)

print("\n=== SUÍTE DE TESTES INTEGRADOS CONCLUÍDA COM SUCESSO! ===")
