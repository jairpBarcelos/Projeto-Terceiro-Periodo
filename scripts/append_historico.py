"""Script auxiliar: appenda historico_aluno_service ao alunos_service.py."""
import pathlib

TARGET = pathlib.Path('backend/services/alunos_service.py')

CODE = """

# ---------------------------------------------------------------------------
# Historico completo do aluno
# ---------------------------------------------------------------------------

def historico_aluno_service(aluno_id: int) -> dict:
    from backend.models import Triagem, Relatorio

    aluno = Aluno.query.get_or_404(aluno_id)

    LABEL_MAP = {
        'atencao': 'Atencao', 'memoria': 'Memoria', 'raciocinio_logico': 'Raciocinio Logico',
        'organizacao': 'Organizacao', 'resolucao_problemas': 'Resolucao de Problemas',
        'leitura': 'Leitura', 'escrita': 'Escrita', 'interpretacao': 'Interpretacao',
        'matematica': 'Matematica', 'coord_motora_fina': 'Coord. Motora Fina',
        'interacao_social': 'Interacao Social', 'hiperatividade': 'Hiperatividade',
        'impulsividade': 'Impulsividade', 'rotina': 'Rotina', 'comunicacao': 'Comunicacao',
        'ansiedade': 'Ansiedade', 'frustracao': 'Frustracao', 'autoestima': 'Autoestima',
        'regulacao_emocional': 'Regulacao Emocional',
    }
    STATUS_MAP = {
        'aguardando_entrevista': 'Aguardando Entrevista', 'em_avaliacao': 'Em Avaliacao',
        'concluida': 'Concluida', 'alta_prioridade': 'Alta Prioridade',
    }

    triagens_raw = (
        Triagem.query.filter(Triagem.aluno_id == aluno_id)
        .order_by(Triagem.data_registro.desc()).all()
    )
    triagens, avaliacoes, evolucoes, obs_comp = [], [], [], []

    for t in triagens_raw:
        psico = t.psicopedagogo.nome_completo if t.psicopedagogo else None
        data = t.data_registro.isoformat() if t.data_registro else None
        av = t.avaliacoes_json or {}

        triagens.append({'id': t.id, 'data': data, 'tipo': t.tipo_registro,
            'status': STATUS_MAP.get(t.status, t.status), 'status_raw': t.status,
            'queixa_principal': t.queixa_principal, 'descricao': t.descricao, 'profissional': psico})

        itens = [{'categoria': cat, 'item': LABEL_MAP.get(i, i)}
            for cat, key in [('Cognitiva','cognitiva'),('Pedagogica','pedagogica'),
                             ('Comportamental','comportamental'),('Socioemocional','socioemocional')]
            for i in av.get(key, [])]
        if itens:
            avaliacoes.append({'triagem_id': t.id, 'data': data, 'profissional': psico, 'itens': itens})

        if t.evolucao:
            evolucoes.append({'triagem_id': t.id, 'data': data, 'texto': t.evolucao, 'profissional': psico})

        comp = av.get('comportamental', [])
        if comp or t.observacoes:
            obs_comp.append({'triagem_id': t.id, 'data': data,
                'itens_comportamentais': [LABEL_MAP.get(i, i) for i in comp],
                'observacoes': t.observacoes, 'profissional': psico})

    relatorios_raw = (
        Relatorio.query.filter(Relatorio.aluno_id == aluno_id)
        .order_by(Relatorio.created_at.desc()).all()
    )
    relatorios, relatorios_auto = [], []
    for r in relatorios_raw:
        item = {'id': r.id, 'titulo': r.titulo, 'tipo': r.tipo, 'origem': r.origem,
            'status': r.status, 'ano_referencia': r.ano_referencia, 'conteudo': r.conteudo,
            'created_at': r.created_at.isoformat() if r.created_at else None}
        relatorios.append(item)
        if r.origem == 'automatico':
            relatorios_auto.append(item)

    return {
        'aluno': {'id': aluno.id, 'nome': aluno.nome_completo,
            'data_nascimento': aluno.data_nascimento.isoformat() if aluno.data_nascimento else None,
            'serie_turma': aluno.serie_turma, 'responsavel': aluno.responsavel_nome,
            'unidade': aluno.unidade.nome if aluno.unidade else None,
            'categorias': [c.nome for c in (aluno.categorias or [])]},
        'triagens': triagens,
        'avaliacoes': avaliacoes,
        'relatorios': relatorios,
        'evolucoes': evolucoes,
        'observacoes_comportamentais': obs_comp,
        'relatorios_automaticos': relatorios_auto,
        'resumo': {
            'total_triagens': len(triagens),
            'total_avaliacoes': len(avaliacoes),
            'total_relatorios': len(relatorios),
            'total_relatorios_auto': len(relatorios_auto),
        },
    }
"""

existing = TARGET.read_text(encoding='utf-8')
if 'historico_aluno_service' not in existing:
    with open(TARGET, 'a', encoding='utf-8') as f:
        f.write(CODE)
    print('OK: historico_aluno_service adicionado.')
else:
    print('JA EXISTE: nenhuma alteracao feita.')
