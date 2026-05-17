"""Injeta a secao Historico do Aluno em triagensAvaliacoes.html."""
import pathlib

HTML = pathlib.Path('frontend/pages/menus/psicopedagogo/triagensAvaliacoes.html')
txt = HTML.read_text(encoding='utf-8')

SECTION = """
<section class="psicoBloco" aria-label="Historico do aluno" style="margin-left:calc(25% + 24px);margin-right:24px;max-width:none;width:auto">
  <h3 style="color:#163a63;margin-bottom:6px">&#128194; Hist&#243;rico do Aluno</h3>
  <p class="psicoInfo">Selecione um aluno para visualizar triagens, avalia&#231;&#245;es, evolu&#231;&#227;o, observa&#231;&#245;es e relat&#243;rios.</p>
  <div class="row g-3 mb-4" style="align-items:flex-end">
    <div class="col-md-6">
      <label class="form-label fw-semibold" for="selectHistoricoAluno">Aluno</label>
      <select id="selectHistoricoAluno" class="form-select">
        <option value="">Selecione o aluno...</option>
      </select>
    </div>
    <div class="col-md-auto">
      <button id="btnCarregarHistorico" class="btn btn-primary">Carregar Hist&#243;rico</button>
    </div>
  </div>
  <div id="aluno-card" class="hist-aluno-card" style="display:none"></div>
  <div id="hist-tabs-wrapper" style="display:none">
    <ul class="nav nav-tabs" id="histTabs" role="tablist">
      <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#tab-triagens" type="button">Triagens <span id="badge-triagens" class="badge bg-primary ms-1">0</span></button></li>
      <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-avaliacoes" type="button">Avalia&#231;&#245;es <span id="badge-avaliacoes" class="badge bg-secondary ms-1">0</span></button></li>
      <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-evolucao" type="button">Evolu&#231;&#227;o <span id="badge-evolucao" class="badge bg-success ms-1">0</span></button></li>
      <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-obs" type="button">Observa&#231;&#245;es <span id="badge-obs" class="badge bg-warning ms-1">0</span></button></li>
      <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-relatorios" type="button">Relat&#243;rios <span id="badge-relatorios" class="badge bg-info ms-1">0</span></button></li>
      <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-auto" type="button">Auto&#45;Relat&#243;rios <span id="badge-auto" class="badge bg-dark ms-1">0</span></button></li>
    </ul>
    <div class="tab-content hist-tab-content" id="histTabContent">
      <div class="tab-pane fade show active" id="tab-triagens" role="tabpanel"><div id="hist-triagens-body"></div></div>
      <div class="tab-pane fade" id="tab-avaliacoes" role="tabpanel"><div id="hist-avaliacoes-body"></div></div>
      <div class="tab-pane fade" id="tab-evolucao" role="tabpanel"><div id="hist-evolucao-body"></div></div>
      <div class="tab-pane fade" id="tab-obs" role="tabpanel"><div id="hist-obs-body"></div></div>
      <div class="tab-pane fade" id="tab-relatorios" role="tabpanel"><div id="hist-relatorios-body"></div></div>
      <div class="tab-pane fade" id="tab-auto" role="tabpanel"><div id="hist-auto-body"></div></div>
    </div>
  </div>
</section>
"""

JS = """
// === HISTORICO DO ALUNO ===
async function popularSelectHistorico() {
  const sel = document.getElementById('selectHistoricoAluno');
  try {
    const r = await fetch(API + '/api/triagens/alunos-select', { headers: authHeaders() });
    const d = await r.json();
    (d.alunos || []).forEach(function(a) {
      const opt = document.createElement('option');
      opt.value = a.id;
      opt.textContent = a.nome + (a.serie_turma ? ' -- ' + a.serie_turma : '');
      sel.appendChild(opt);
    });
  } catch(e) {}
}

function dataFmt(d) {
  if (!d) return '--';
  return new Date(d + 'T00:00').toLocaleDateString('pt-BR');
}

function vazio(msg) { return '<p class="text-muted py-3 text-center">' + msg + '</p>'; }

function statusBadge(s) {
  var cor = { aguardando_entrevista:'#4c7adf', em_avaliacao:'#0f9d93', concluida:'#2e7d32', alta_prioridade:'#e14e5b', rascunho:'#888', publicado:'#2e7d32', arquivado:'#999' };
  var c = cor[s] || '#888';
  return '<span style="background:' + c + '20;color:' + c + ';padding:2px 10px;border-radius:999px;font-size:.8rem;font-weight:600">' + s + '</span>';
}

async function carregarHistorico() {
  var aluno_id = document.getElementById('selectHistoricoAluno').value;
  if (!aluno_id) { alert('Selecione um aluno.'); return; }
  var btn = document.getElementById('btnCarregarHistorico');
  btn.disabled = true; btn.textContent = 'Carregando...';
  try {
    var r = await fetch(API + '/api/alunos/historico/' + aluno_id, { headers: authHeaders() });
    if (!r.ok) { alert('Erro ao carregar historico.'); return; }
    var d = await r.json();
    renderHistorico(d);
  } catch(e) { alert('Erro de conexao.'); }
  finally { btn.disabled = false; btn.textContent = 'Carregar Historico'; }
}

function renderHistorico(d) {
  var a = d.aluno || {};
  var card = document.getElementById('aluno-card');
  card.style.display = 'flex';
  card.innerHTML = '<div class="hist-aluno-info"><strong>' + a.nome + '</strong><span>' +
    (a.serie_turma || 'Serie nao informada') + '</span><span>Responsavel: ' + (a.responsavel || '--') + '</span>' +
    '<span>Unidade: ' + (a.unidade || '--') + '</span></div>' +
    '<div class="hist-aluno-tags">' +
    (a.categorias || []).map(function(c){ return '<span class="hist-tag">' + c + '</span>'; }).join('') +
    (!(a.categorias || []).length ? '<span class="text-muted small">Sem categorias</span>' : '') + '</div>';

  document.getElementById('hist-tabs-wrapper').style.display = 'block';
  document.getElementById('badge-triagens').textContent = d.triagens.length;
  document.getElementById('badge-avaliacoes').textContent = d.avaliacoes.length;
  document.getElementById('badge-evolucao').textContent = d.evolucoes.length;
  document.getElementById('badge-obs').textContent = d.observacoes_comportamentais.length;
  document.getElementById('badge-relatorios').textContent = d.relatorios.length;
  document.getElementById('badge-auto').textContent = d.relatorios_automaticos.length;

  document.getElementById('hist-triagens-body').innerHTML = d.triagens.length
    ? '<div class="table-responsive"><table class="table table-striped align-middle mt-3"><thead><tr><th>Data</th><th>Tipo</th><th>Status</th><th>Queixa Principal</th><th>Profissional</th></tr></thead><tbody>' +
      d.triagens.map(function(t){ return '<tr><td>' + dataFmt(t.data) + '</td><td>' + t.tipo + '</td><td>' + statusBadge(t.status) + '</td><td style="max-width:240px">' +
      (t.queixa_principal || '<em class="text-muted">--</em>') + '</td><td>' + (t.profissional || '--') + '</td></tr>'; }).join('') + '</tbody></table></div>'
    : vazio('Nenhuma triagem registrada para este aluno.');

  document.getElementById('hist-avaliacoes-body').innerHTML = d.avaliacoes.length
    ? d.avaliacoes.map(function(av){ return '<div class="hist-av-bloco"><div class="hist-av-meta">' + dataFmt(av.data) + ' - ' + (av.profissional||'--') + '</div><div class="hist-av-itens">' +
      av.itens.map(function(i){ return '<span class="hist-av-tag">[' + i.categoria + '] ' + i.item + '</span>'; }).join('') + '</div></div>'; }).join('')
    : vazio('Nenhuma avaliacao com itens marcados.');

  document.getElementById('hist-evolucao-body').innerHTML = d.evolucoes.length
    ? d.evolucoes.map(function(e){ return '<div class="hist-linha"><div class="hist-linha-data">' + dataFmt(e.data) + '</div><div class="hist-linha-body"><p class="mb-1">' +
      (e.texto || '').replace(/\n/g,'<br>') + '</p><small class="text-muted">' + (e.profissional||'--') + '</small></div></div>'; }).join('')
    : vazio('Nenhum registro de evolucao encontrado.');

  document.getElementById('hist-obs-body').innerHTML = d.observacoes_comportamentais.length
    ? d.observacoes_comportamentais.map(function(o){ return '<div class="hist-linha"><div class="hist-linha-data">' + dataFmt(o.data) + '</div><div class="hist-linha-body">' +
      (o.itens_comportamentais.length ? '<div class="mb-2">' + o.itens_comportamentais.map(function(i){ return '<span class="badge bg-warning text-dark me-1">' + i + '</span>'; }).join('') + '</div>' : '') +
      (o.observacoes ? '<p class="mb-1">' + o.observacoes.replace(/\n/g,'<br>') + '</p>' : '') +
      '<small class="text-muted">' + (o.profissional||'--') + '</small></div></div>'; }).join('')
    : vazio('Nenhuma observacao comportamental registrada.');

  function renderRels(lista, elId) {
    document.getElementById(elId).innerHTML = lista.length
      ? '<div class="table-responsive"><table class="table table-striped align-middle mt-3"><thead><tr><th>Titulo</th><th>Tipo</th><th>Origem</th><th>Status</th><th>Data</th></tr></thead><tbody>' +
        lista.map(function(r){ return '<tr><td>' + r.titulo + '</td><td>' + r.tipo + '</td><td>' + r.origem + '</td><td>' + statusBadge(r.status) + '</td><td>' +
        (r.created_at ? new Date(r.created_at).toLocaleDateString('pt-BR') : '--') + '</td></tr>'; }).join('') + '</tbody></table></div>'
      : vazio('Nenhum relatorio encontrado.');
  }
  renderRels(d.relatorios, 'hist-relatorios-body');
  renderRels(d.relatorios_automaticos, 'hist-auto-body');
}

document.getElementById('btnCarregarHistorico').addEventListener('click', carregarHistorico);
popularSelectHistorico();
"""

MARKER_HTML = '<div vw class="enabled">'
MARKER_JS = '</script>'

if 'selectHistoricoAluno' not in txt:
    txt = txt.replace(MARKER_HTML, SECTION + MARKER_HTML, 1)
    last = txt.rfind(MARKER_JS)
    txt = txt[:last] + JS + txt[last:]
    HTML.write_text(txt, encoding='utf-8')
    print('OK: historico injetado')
else:
    print('JA EXISTE')
