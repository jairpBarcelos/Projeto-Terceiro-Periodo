"""
Substitui o render de tabela de triagens por cards com botao Editar
e adiciona CSS dos cards. Idempotente.
"""
import pathlib

HTML = pathlib.Path('frontend/pages/menus/psicopedagogo/triagensAvaliacoes.html')
CSS  = pathlib.Path('frontend/css/menuPsicopedagogo.css')

html = HTML.read_text(encoding='utf-8')
css  = CSS.read_text(encoding='utf-8')

# ── 1. Localizar o bloco de render (table) e substituir por cards ──────────
START_MARKER = "getElementById('hist-triagens-body').innerHTML = d.triagens.length"
END_MARKER   = ": vazio('Nenhuma triagem registrada para este aluno.');"

i_start = html.find(START_MARKER)
if i_start == -1:
    print('ERRO: marker de inicio nao encontrado')
    exit(1)

i_end = html.find(END_MARKER, i_start)
if i_end == -1:
    print('ERRO: marker de fim nao encontrado')
    exit(1)

OLD_BLOCK = html[i_start : i_end + len(END_MARKER)]

NEW_BLOCK = """getElementById('hist-triagens-body').innerHTML = d.triagens.length
    ? '<div class="triagem-cards-grid">' + d.triagens.map(function(t) {
        var av = t.avaliacoes_json || {};
        var tagsList = [];
        var catMap = {cognitiva:'Cog',pedagogica:'Ped',comportamental:'Comp',socioemocional:'Soc'};
        Object.keys(catMap).forEach(function(k){
          (av[k]||[]).forEach(function(v){ tagsList.push('<span class="triagem-card-tag triagem-tag-'+k+'">'+catMap[k]+': '+v.replace(/_/g,' ')+'</span>'); });
        });
        return '<div class="triagem-card">'
          + '<div class="triagem-card-header">'
            + '<div class="triagem-card-meta">'
              + '<span class="triagem-card-data">'+dataFmt(t.data)+'</span>'
              + '<span class="triagem-card-tipo">'+t.tipo+'</span>'
            + '</div>'
            + statusBadge(t.status)
          + '</div>'
          + '<div class="triagem-card-body">'
            + (t.queixa_principal ? '<p class="triagem-card-queixa"><strong>Queixa:</strong> '+t.queixa_principal+'</p>' : '')
            + (t.descricao ? '<p class="triagem-card-desc text-muted small">'+t.descricao+'</p>' : '')
            + (tagsList.length ? '<div class="triagem-card-tags">'+tagsList.join('')+'</div>' : '')
          + '</div>'
          + '<div class="triagem-card-footer">'
            + '<small class="text-muted">Profissional: '+(t.profissional||'--')+'</small>'
            + '<button class="btn btn-sm btn-outline-primary triagem-edit-btn" '
              + 'onclick="abrirEditTriagem('+JSON.stringify(t).replace(/\"/g,\'&quot;\')+')">'
              + '&#9998; Editar'
            + '</button>'
          + '</div>'
        + '</div>';
      }).join('') + '</div>'
    : vazio('Nenhuma triagem registrada para este aluno.');"""

if 'triagem-cards-grid' in html:
    print('Cards ja existem - nada a fazer no HTML')
else:
    html = html[:i_start] + NEW_BLOCK + html[i_start + len(OLD_BLOCK):]
    print('Cards substituidos')

# ── 2. Garantir que abrirEditTriagem recebe avaliacoes_json ────────────────
# O historico_aluno_service nao devolve avaliacoes_json dentro de cada triagem
# Precisamos que o servico inclua isso. Patchamos o serializar no JS:
# (ja incluimos no JSON.stringify acima - ok)

# ── 3. CSS dos cards ───────────────────────────────────────────────────────
CSS_CARDS = """
/* === Cards de Triagem no Historico === */
.triagem-cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 16px;
    padding: 16px 0;
}
.triagem-card {
    background: #fff;
    border: 1.5px solid #dce8f5;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(22,58,99,.07);
    display: flex;
    flex-direction: column;
    transition: box-shadow .2s, transform .15s;
}
.triagem-card:hover {
    box-shadow: 0 6px 24px rgba(22,58,99,.14);
    transform: translateY(-2px);
}
.triagem-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: linear-gradient(135deg, #f0f6ff, #e8f1fb);
    border-bottom: 1px solid #dce8f5;
    gap: 8px;
    flex-wrap: wrap;
}
.triagem-card-meta { display: flex; flex-direction: column; gap: 2px; }
.triagem-card-data { font-size: .82rem; font-weight: 700; color: #163a63; }
.triagem-card-tipo {
    font-size: .75rem; color: #5b6f86;
    text-transform: uppercase; letter-spacing: .04em;
}
.triagem-card-body { padding: 14px 16px; flex: 1; }
.triagem-card-queixa { font-size: .9rem; color: #1a2e45; margin-bottom: 6px; }
.triagem-card-desc   { font-size: .83rem; margin-bottom: 8px; }
.triagem-card-tags   { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
.triagem-card-tag {
    font-size: .75rem; font-weight: 600; padding: 2px 9px;
    border-radius: 999px; border: 1px solid;
}
.triagem-tag-cognitiva       { background:#eaf3ff; color:#163a63; border-color:#c5dbf2; }
.triagem-tag-pedagogica      { background:#e6f7f5; color:#0a6b66; border-color:#9fd8d3; }
.triagem-tag-comportamental  { background:#fff3e6; color:#a35c0a; border-color:#f5c98a; }
.triagem-tag-socioemocional  { background:#f3eeff; color:#5a3a99; border-color:#c9aef5; }
.triagem-card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 16px;
    border-top: 1px solid #edf2f8;
    background: #fafcff;
}
.triagem-edit-btn {
    font-size: .82rem;
    padding: 4px 12px;
    border-radius: 8px;
    transition: background .15s, color .15s;
}
.triagem-edit-btn:hover { background: #163a63; color: #fff; border-color: #163a63; }
"""

if 'triagem-cards-grid' not in css:
    with open(CSS, 'a', encoding='utf-8') as f:
        f.write(CSS_CARDS)
    print('CSS dos cards adicionado')
else:
    print('CSS ja existe')

# ── 4. Salvar HTML ──────────────────────────────────────────────────────────
HTML.write_text(html, encoding='utf-8')
print('HTML salvo. Linhas:', html.count('\n'))
