/**
 * relatoriosPsicopedagogo.js
 * Controlador completo do módulo de Relatórios Psicopedagógicos.
 * Cobre: dashboard, listagem, filtros, paginação, criação/edição,
 * visualização formal, exportação PDF (via print) e exclusão.
 */

(function () {
  'use strict';

  // ───────────────────────────────────────────────────────────────────────────
  // Estado global
  // ───────────────────────────────────────────────────────────────────────────
  let _paginaAtual = 1;
  const LIMITE = 12;
  let _unidadeId   = null;
  let _nomeUsuario = '';

  // Instâncias Bootstrap Modal
  let _modalNovoRel    = null;
  let _modalVizualizar = null;
  let _modalExclusao   = null;

  // ID do relatório sendo visualizado (para exportação PDF)
  let _relatorioAtualId = null;

  // ───────────────────────────────────────────────────────────────────────────
  // Mapeamentos de label
  // ───────────────────────────────────────────────────────────────────────────
  const TIPO_LABEL = {
    evolucao:       'Relatório de Evolução',
    encaminhamento: 'Relatório de Encaminhamento',
    sintese:        'Síntese Semestral',
    familia:        'Relatório para Família',
    parecer:        'Parecer Técnico',
    laudo:          'Laudo Psicopedagógico',
  };

  const STATUS_LABEL = {
    emitido:  'Emitido',
    rascunho: 'Rascunho',
  };

  // ───────────────────────────────────────────────────────────────────────────
  // Utilitários
  // ───────────────────────────────────────────────────────────────────────────

  /** Escapa strings contra XSS. */
  function esc(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g,  '&amp;')
      .replace(/</g,  '&lt;')
      .replace(/>/g,  '&gt;')
      .replace(/"/g,  '&quot;')
      .replace(/'/g,  '&#039;');
  }

  /** Formata data ISO (ou YYYY-MM-DD) → dd/mm/aaaa. */
  function fmtData(iso) {
    if (!iso) return '—';
    const s = String(iso).split('T')[0];
    const [y, m, d] = s.split('-');
    if (!y || !m || !d) return iso;
    return `${d}/${m}/${y}`;
  }

  /** Preenche textContent de um elemento pelo id. */
  function setTexto(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val ?? '—';
  }

  /** Toast flutuante de feedback. */
  function toast(msg, tipo = 'success') {
    const el = document.createElement('div');
    el.className = `alert alert-${tipo} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    el.style.cssText = 'z-index:9999;min-width:280px;box-shadow:0 4px 16px rgba(0,0,0,.15)';
    el.innerHTML = `${esc(msg)}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>`;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 5000);
  }

  /** Badge de status. */
  function badgeStatus(status) {
    const mapa = { emitido: 'bg-success', rascunho: 'bg-warning text-dark' };
    const cls   = mapa[status] ?? 'bg-secondary';
    const label = STATUS_LABEL[status] ?? status;
    return `<span class="badge ${cls}">${esc(label)}</span>`;
  }

  /** Período formatado "de/até". */
  function fmtPeriodo(ini, fim) {
    if (!ini && !fim) return '—';
    if (!fim) return `A partir de ${fmtData(ini)}`;
    if (!ini) return `Até ${fmtData(fim)}`;
    return `${fmtData(ini)} – ${fmtData(fim)}`;
  }

  /** Spinner de carregamento para a tabela. */
  function tbodyCarregando(span = 7) {
    return `<tr><td colspan="${span}" class="text-center text-muted py-4">
      <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
      Carregando…</td></tr>`;
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Perfil do usuário
  // ───────────────────────────────────────────────────────────────────────────

  function preencherPerfil() {
    try {
      const user = JSON.parse(localStorage.getItem('saadi_user_info') || '{}');
      if (!user) return;
      _unidadeId   = user.unidade_id   || null;
      _nomeUsuario = user.nome         || 'Psicopedagogo(a)';
      const el = document.getElementById('nomeUsuario');
      if (el && user.nome) el.textContent = `Bem-vindo(a), ${user.nome.split(' ')[0]}!`;
    } catch { /* silencioso */ }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Sair
  // ───────────────────────────────────────────────────────────────────────────

  function inicializarSair() {
    const btn = document.getElementById('btnSair');
    if (!btn) return;
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      try { await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' }); }
      catch { /* ok */ }
      finally {
        if (window.saadiAuth?.clearTokens) window.saadiAuth.clearTokens();
        window.location.href = '/index.html';
      }
    });
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Dashboard — métricas
  // ───────────────────────────────────────────────────────────────────────────

  async function carregarDashboard() {
    try {
      const resp = await fetch('/api/relatorios/dashboard', {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) return;
      const json = await resp.json();
      const d = json.data ?? json;
      setTexto('totalRelatorios', d.total    ?? '—');
      setTexto('totalEmitidos',   d.emitidos ?? '—');
      setTexto('totalRascunhos',  d.rascunhos ?? '—');
    } catch (err) {
      console.error('[SAADI] Dashboard relatórios:', err);
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Carregamento de alunos
  // ───────────────────────────────────────────────────────────────────────────

  async function carregarAlunos() {
    const sel = document.getElementById('relAluno');
    if (!sel) return;
    try {
      let url = '/api/alunos?limit=200&status=ativo';
      if (_unidadeId) url += `&unidade_id=${_unidadeId}`;
      const resp = await fetch(url, { credentials: 'same-origin', headers: { Accept: 'application/json' } });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json  = await resp.json();
      const alunos = json.data?.items ?? json.items ?? [];
      const opts   = alunos.map(a =>
        `<option value="${esc(a.id)}">${esc(a.nome_completo)} (RA: ${esc(a.ra ?? '-')})</option>`
      ).join('');
      sel.innerHTML = '<option value="">Selecione um aluno…</option>' + opts;
    } catch (err) {
      console.error('[SAADI] Erro ao carregar alunos:', err);
      sel.innerHTML = '<option value="">Erro ao carregar alunos</option>';
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Tabela de relatórios
  // ───────────────────────────────────────────────────────────────────────────

  async function carregarRelatorios(page = 1, filtros = {}) {
    const tbody = document.querySelector('#tabelaRelatorios tbody');
    if (!tbody) return;

    tbody.innerHTML = tbodyCarregando(7);

    const params = new URLSearchParams({ page, limit: LIMITE, ...filtros });

    try {
      const resp = await fetch(`/api/relatorios?${params}`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">
          <strong>Erro:</strong> Não foi possível carregar os relatórios (HTTP ${resp.status}).</td></tr>`;
        return;
      }

      const json  = await resp.json();
      const items = json.items ?? json.data?.items ?? [];
      const total = json.total ?? json.data?.total ?? 0;

      if (!items.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">
          Nenhum relatório encontrado com os filtros informados.</td></tr>`;
        atualizarPaginacao(0, page, LIMITE);
        return;
      }

      tbody.innerHTML = items.map(r => {
        const tipoLabel = TIPO_LABEL[r.tipo] ?? r.tipo ?? '—';
        const periodo   = fmtPeriodo(r.periodo_inicio, r.periodo_fim);
        const dataCriac = fmtData(r.created_at ?? r.data_criacao);

        const acoes = `
          <div class="acoes-grupo">
            <button class="btn btn-sm btn-outline-primary btn-ver-rel" data-id="${esc(r.id)}"
              title="Visualizar" aria-label="Visualizar relatório">Ver</button>
            <button class="btn btn-sm btn-outline-secondary btn-editar-rel" data-id="${esc(r.id)}"
              title="Editar" aria-label="Editar relatório" ${r.status === 'emitido' ? 'disabled' : ''}>Editar</button>
            <button class="btn btn-sm btn-outline-dark btn-exportar-rel" data-id="${esc(r.id)}"
              title="Exportar PDF" aria-label="Exportar PDF do relatório">PDF</button>
            <button class="btn btn-sm btn-outline-danger btn-excluir-rel"
              data-id="${esc(r.id)}" data-nome="${esc(r.aluno_nome ?? '—')}"
              title="Excluir" aria-label="Excluir relatório">Excluir</button>
          </div>`;

        return `
          <tr>
            <td><strong>${esc(r.aluno_nome ?? '—')}</strong></td>
            <td>${esc(r.turma ?? '—')}</td>
            <td><span class="badge bg-secondary">${esc(tipoLabel)}</span></td>
            <td>${esc(periodo)}</td>
            <td>${badgeStatus(r.status)}</td>
            <td>${esc(dataCriac)}</td>
            <td>${acoes}</td>
          </tr>`;
      }).join('');

      _paginaAtual = page;
      atualizarPaginacao(total, page, LIMITE);
    } catch (err) {
      console.error('[SAADI] Erro ao carregar relatórios:', err);
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">
        Erro de conexão com o servidor.</td></tr>`;
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Paginação
  // ───────────────────────────────────────────────────────────────────────────

  function atualizarPaginacao(total, page, limit) {
    const container = document.getElementById('paginacaoRelatorios');
    if (!container) return;
    const totalPaginas = Math.ceil(total / limit) || 1;
    if (totalPaginas <= 1) { container.innerHTML = ''; return; }

    const prev = page <= 1 ? 'disabled' : '';
    const next = page >= totalPaginas ? 'disabled' : '';

    container.innerHTML = `
      <nav aria-label="Paginação de relatórios">
        <ul class="pagination pagination-sm mb-0">
          <li class="page-item ${prev}">
            <button class="page-link" id="relBtnAnterior" aria-label="Página anterior">Anterior</button>
          </li>
          <li class="page-item disabled">
            <span class="page-link">${page} / ${totalPaginas}</span>
          </li>
          <li class="page-item ${next}">
            <button class="page-link" id="relBtnProxima" aria-label="Próxima página">Próxima</button>
          </li>
        </ul>
      </nav>`;

    document.getElementById('relBtnAnterior')
      ?.addEventListener('click', () => carregarRelatorios(page - 1, coletarFiltros()));
    document.getElementById('relBtnProxima')
      ?.addEventListener('click', () => carregarRelatorios(page + 1, coletarFiltros()));
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Filtros
  // ───────────────────────────────────────────────────────────────────────────

  function coletarFiltros() {
    const filtros = {};
    const q      = document.getElementById('filtroBuscaRel')?.value?.trim();
    const de     = document.getElementById('filtroPeriodoDe')?.value;
    const ate    = document.getElementById('filtroPeriodoAte')?.value;
    const tipo   = document.getElementById('filtroTipoRel')?.value;
    const status = document.getElementById('filtroStatusRel')?.value;
    if (q)      filtros.q              = q;
    if (de)     filtros.periodo_inicio = de;
    if (ate)    filtros.periodo_fim    = ate;
    if (tipo)   filtros.tipo           = tipo;
    if (status) filtros.status         = status;
    return filtros;
  }

  function inicializarFiltros() {
    const form = document.getElementById('formFiltrosRel');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        carregarRelatorios(1, coletarFiltros());
      });
    }
    document.getElementById('btnLimparFiltrosRel')?.addEventListener('click', () => {
      form?.reset();
      carregarRelatorios(1);
    });
    document.getElementById('filtroBuscaRel')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') carregarRelatorios(1, coletarFiltros());
    });
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Delegação de ações na tabela
  // ───────────────────────────────────────────────────────────────────────────

  function inicializarTabelaAcoes() {
    const tbody = document.querySelector('#tabelaRelatorios tbody');
    if (!tbody) return;

    tbody.addEventListener('click', (e) => {
      const btnVer     = e.target.closest('.btn-ver-rel');
      const btnEditar  = e.target.closest('.btn-editar-rel');
      const btnPDF     = e.target.closest('.btn-exportar-rel');
      const btnExcluir = e.target.closest('.btn-excluir-rel');

      if (btnVer)     abrirVisualizador(btnVer.dataset.id);
      if (btnEditar)  abrirEdicao(btnEditar.dataset.id);
      if (btnPDF)     exportarPDF(btnPDF.dataset.id);
      if (btnExcluir) confirmarExclusao(btnExcluir.dataset.id, btnExcluir.dataset.nome);
    });
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Modal: Novo / Editar Relatório
  // ───────────────────────────────────────────────────────────────────────────

  function getModalNovoRel() {
    if (!_modalNovoRel) {
      const el = document.getElementById('modalNovoRelatorio');
      if (el) _modalNovoRel = new bootstrap.Modal(el);
    }
    return _modalNovoRel;
  }

  function limparFormNovoRel() {
    const form = document.getElementById('formNovoRel');
    if (form) { form.reset(); delete form.dataset.editId; }
    document.getElementById('relEditandoId').value = '';
    document.getElementById('modalNovoRelTitulo').textContent = 'Novo Relatório Psicopedagógico';
    document.getElementById('modalNovoRelSubtitulo').textContent =
      'Preencha os campos e salve como rascunho ou emita oficialmente.';
  }

  function inicializarResetModalNovoRel() {
    document.getElementById('modalNovoRelatorio')
      ?.addEventListener('hidden.bs.modal', limparFormNovoRel);
  }

  async function abrirEdicao(id) {
    try {
      const resp = await fetch(`/api/relatorios/${id}`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) { toast('Não foi possível carregar o relatório para edição.', 'danger'); return; }
      const json = await resp.json();
      const r    = json.data?.item ?? json.item ?? json;
      if (!r)    { toast('Dados do relatório não encontrados.', 'danger'); return; }

      if (r.status === 'emitido') {
        toast('Relatórios já emitidos não podem ser editados.', 'warning');
        return;
      }

      const setVal = (elId, val) => {
        const el = document.getElementById(elId);
        if (el) el.value = val ?? '';
      };

      setVal('relEditandoId',    r.id);
      setVal('relAluno',         r.aluno_id);
      setVal('relTurma',         r.turma);
      setVal('relTipo',          r.tipo);
      setVal('relStatus',        r.status);
      setVal('relPeriodoDe',     (r.periodo_inicio ?? '').substring(0, 10));
      setVal('relPeriodoAte',    (r.periodo_fim    ?? '').substring(0, 10));
      setVal('relHistorico',     r.secao_historico      ?? r.historico     ?? '');
      setVal('relIntervencoes',  r.secao_intervencoes   ?? r.intervencoes  ?? '');
      setVal('relEvolucao',      r.secao_evolucao       ?? r.evolucao      ?? r.conteudo ?? '');
      setVal('relEncaminhamentos',r.secao_encaminhamentos ?? r.encaminhamentos ?? '');
      setVal('relRecomendacoes', r.secao_recomendacoes  ?? r.recomendacoes ?? '');
      setVal('relObservacoes',   r.observacoes ?? '');

      document.getElementById('modalNovoRelTitulo').textContent  = 'Editar Relatório';
      document.getElementById('modalNovoRelSubtitulo').textContent = 'Altere as informações e salve.';

      getModalNovoRel()?.show();
    } catch (err) {
      console.error('[SAADI] Erro ao abrir edição de relatório:', err);
      toast('Erro de conexão ao carregar relatório.', 'danger');
    }
  }

  function inicializarFormNovoRel() {
    const form = document.getElementById('formNovoRel');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const editId      = document.getElementById('relEditandoId')?.value || null;
      const alunoId     = document.getElementById('relAluno')?.value;
      const turma       = document.getElementById('relTurma')?.value?.trim() || null;
      const tipo        = document.getElementById('relTipo')?.value;
      const status      = document.getElementById('relStatus')?.value;
      const periodoDe   = document.getElementById('relPeriodoDe')?.value  || null;
      const periodoAte  = document.getElementById('relPeriodoAte')?.value || null;
      const historico   = document.getElementById('relHistorico')?.value?.trim()      || null;
      const intervencoes = document.getElementById('relIntervencoes')?.value?.trim()  || null;
      const evolucao    = document.getElementById('relEvolucao')?.value?.trim()       || null;
      const encaminhamentos = document.getElementById('relEncaminhamentos')?.value?.trim() || null;
      const recomendacoes = document.getElementById('relRecomendacoes')?.value?.trim() || null;
      const observacoes = document.getElementById('relObservacoes')?.value?.trim()    || null;

      if (!alunoId) { toast('Selecione um aluno.', 'warning'); return; }
      if (!tipo)    { toast('Selecione o tipo de relatório.', 'warning'); return; }
      if (!evolucao){ toast('Preencha a seção "Evolução Observada".', 'warning'); return; }
      if (!recomendacoes){ toast('Preencha a seção "Recomendações".', 'warning'); return; }

      const payload = {
        aluno_id:               parseInt(alunoId, 10),
        turma,
        tipo,
        status,
        periodo_inicio:         periodoDe,
        periodo_fim:            periodoAte,
        secao_historico:        historico,
        secao_intervencoes:     intervencoes,
        secao_evolucao:         evolucao,
        secao_encaminhamentos:  encaminhamentos,
        secao_recomendacoes:    recomendacoes,
        observacoes,
        // Compatibilidade com backend legado que usa campo único "conteudo"
        conteudo: [
          historico       ? `1. HISTÓRICO\n${historico}` : null,
          intervencoes    ? `2. INTERVENÇÕES\n${intervencoes}` : null,
          evolucao        ? `3. EVOLUÇÃO\n${evolucao}` : null,
          encaminhamentos ? `4. ENCAMINHAMENTOS\n${encaminhamentos}` : null,
          recomendacoes   ? `5. RECOMENDAÇÕES\n${recomendacoes}` : null,
        ].filter(Boolean).join('\n\n'),
      };

      const isEdicao = Boolean(editId);
      const url    = isEdicao ? `/api/relatorios/${editId}` : '/api/relatorios';
      const method = isEdicao ? 'PUT' : 'POST';

      const btnSalvar = document.getElementById('btnSalvarNovoRel');
      const txtOrig   = btnSalvar?.textContent;

      try {
        if (btnSalvar) {
          btnSalvar.disabled = true;
          btnSalvar.innerHTML =
            '<span class="spinner-border spinner-border-sm" role="status"></span> Salvando…';
        }

        const resp = await fetch(url, {
          method,
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify(payload),
        });

        const json = await resp.json();
        if (!resp.ok) { toast(json.message || 'Erro ao salvar relatório.', 'danger'); return; }

        getModalNovoRel()?.hide();
        toast(isEdicao ? 'Relatório atualizado com sucesso!' : 'Relatório salvo com sucesso!', 'success');
        carregarDashboard();
        carregarRelatorios(_paginaAtual, coletarFiltros());
      } catch (err) {
        console.error('[SAADI] Erro ao salvar relatório:', err);
        toast('Erro de conexão ao salvar relatório.', 'danger');
      } finally {
        if (btnSalvar) { btnSalvar.disabled = false; btnSalvar.textContent = txtOrig; }
      }
    });
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Modal: Visualizar relatório (documento formal)
  // ───────────────────────────────────────────────────────────────────────────

  function getModalVisualizar() {
    if (!_modalVizualizar) {
      const el = document.getElementById('modalVisualizarRelatorio');
      if (el) _modalVizualizar = new bootstrap.Modal(el);
    }
    return _modalVizualizar;
  }

  /** Preenche seção do relatório formal ou marca como vazia. */
  function preencherSecao(textoElId, secaoElId, texto) {
    const textoEl = document.getElementById(textoElId);
    const secEl   = document.getElementById(secaoElId);
    const vazio   = !texto || !texto.trim();
    if (textoEl) textoEl.textContent = vazio ? 'Não registrado.' : texto;
    if (secEl)   secEl.classList.toggle('rel-secao-vazia', vazio);
  }

  async function abrirVisualizador(id) {
    const modal = getModalVisualizar();
    if (!modal) return;

    // Mostra modal com skeleton imediatamente
    const corpo = document.getElementById('corpoModalVisualizar');

    _relatorioAtualId = id;
    modal.show();

    try {
      const resp = await fetch(`/api/relatorios/${id}`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) {
        toast(`Erro ao carregar relatório (HTTP ${resp.status}).`, 'danger');
        return;
      }

      const json = await resp.json();
      const r    = json.data?.item ?? json.item ?? json;
      if (!r) { toast('Dados do relatório não encontrados.', 'danger'); return; }

      // Título e subtítulo do modal
      const tipoLabel = TIPO_LABEL[r.tipo] ?? r.tipo ?? '—';
      document.getElementById('modalVisualizarTitulo').textContent = tipoLabel;
      document.getElementById('vRelatorioSubtitulo').textContent   =
        `${r.aluno_nome ?? '—'} — ${fmtPeriodo(r.periodo_inicio, r.periodo_fim)}`;

      // Cabeçalho do documento
      document.getElementById('vDocTitulo').textContent = tipoLabel;

      // Metadados
      setTexto('vRelAluno',       r.aluno_nome ?? '—');
      setTexto('vRelTurma',       r.turma ?? '—');
      setTexto('vRelTipo',        tipoLabel);
      setTexto('vRelPeriodo',     fmtPeriodo(r.periodo_inicio, r.periodo_fim));
      setTexto('vRelDataCriacao', fmtData(r.created_at ?? r.data_criacao));
      setTexto('vRelAutor',       r.autor_nome ?? _nomeUsuario ?? '—');
      setTexto('vRelDataImpressao', new Date().toLocaleDateString('pt-BR', { dateStyle: 'long' }));

      // Badge de status
      const statusEl = document.getElementById('vRelStatus');
      if (statusEl) statusEl.innerHTML = badgeStatus(r.status);

      // Resolve conteúdo das seções
      // Tenta primeiro os campos de seção estruturados, depois o conteúdo legado
      const legado = r.conteudo ?? '';
      preencherSecao('vRelHistorico',        'vSecHistorico',
        r.secao_historico      ?? r.historico     ?? extrairSecaoLegado(legado, 'historico'));
      preencherSecao('vRelIntervencoes',     'vSecIntervencoes',
        r.secao_intervencoes   ?? r.intervencoes  ?? extrairSecaoLegado(legado, 'intervencoes'));
      preencherSecao('vRelEvolucao',         'vSecEvolucao',
        r.secao_evolucao       ?? r.evolucao      ?? extrairSecaoLegado(legado, 'evolucao') ?? legado);
      preencherSecao('vRelEncaminhamentos',  'vSecEncaminhamentos',
        r.secao_encaminhamentos ?? r.encaminhamentos ?? extrairSecaoLegado(legado, 'encaminhamentos'));
      preencherSecao('vRelRecomendacoes',    'vSecRecomendacoes',
        r.secao_recomendacoes  ?? r.recomendacoes ?? extrairSecaoLegado(legado, 'recomendacoes'));

      // Observações adicionais (oculto se vazio)
      const obs      = r.observacoes ?? '';
      const secObs   = document.getElementById('vSecObservacoes');
      const textoObs = document.getElementById('vRelObservacoes');
      if (obs.trim()) {
        if (secObs)   secObs.style.display = 'block';
        if (textoObs) textoObs.textContent  = obs;
      } else {
        if (secObs) secObs.style.display = 'none';
      }
    } catch (err) {
      console.error('[SAADI] Erro ao visualizar relatório:', err);
      toast('Erro de conexão ao carregar relatório.', 'danger');
    }
  }

  /** Tenta extrair uma seção de um texto de conteúdo legado concatenado. */
  function extrairSecaoLegado(conteudo, chave) {
    if (!conteudo) return null;
    const mapaRegex = {
      historico:        /1\.\s*HIST[ÓO]RICO\s*\n([\s\S]*?)(?=\n2\.|$)/i,
      intervencoes:     /2\.\s*INTERVEN[ÇC][ÕO]ES\s*\n([\s\S]*?)(?=\n3\.|$)/i,
      evolucao:         /3\.\s*EVOLU[ÇC][ÃA]O\s*\n([\s\S]*?)(?=\n4\.|$)/i,
      encaminhamentos:  /4\.\s*ENCAMINHAMENTOS\s*\n([\s\S]*?)(?=\n5\.|$)/i,
      recomendacoes:    /5\.\s*RECOMENDA[ÇC][ÕO]ES\s*\n([\s\S]*?)$/i,
    };
    const regex = mapaRegex[chave];
    if (!regex) return null;
    const match = conteudo.match(regex);
    return match ? match[1].trim() : null;
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Exportar PDF (via window.print com área de impressão dedicada)
  // ───────────────────────────────────────────────────────────────────────────

  async function exportarPDF(id) {
    const relId = id ?? _relatorioAtualId;
    if (!relId) { toast('Nenhum relatório selecionado para exportar.', 'warning'); return; }

    try {
      const resp = await fetch(`/api/relatorios/${relId}`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json = await resp.json();
      const r    = json.data?.item ?? json.item ?? json;
      if (!r)  throw new Error('Dados não encontrados.');

      const tipoLabel = TIPO_LABEL[r.tipo] ?? r.tipo ?? '—';
      const agora     = new Date().toLocaleDateString('pt-BR', { dateStyle: 'long' });

      const html = `
        <div style="font-family:'Roboto',sans-serif;color:#1a2e45;padding:20px;max-width:800px;margin:auto;">
          <div style="border-bottom:3px solid #163a63;padding-bottom:16px;margin-bottom:20px;">
            <h2 style="color:#163a63;font-size:1.3rem;margin:0;">${esc(tipoLabel)}</h2>
            <p style="color:#5b6f86;margin:4px 0 0;font-size:.85rem;">
              Sistema SAADI — Gestão Escolar Psicopedagógica
            </p>
          </div>
          <table style="width:100%;border-collapse:collapse;margin-bottom:20px;font-size:.88rem;">
            <tr>
              <td style="padding:6px 0;"><strong>Estudante:</strong> ${esc(r.aluno_nome ?? '—')}</td>
              <td style="padding:6px 0;"><strong>Turma:</strong> ${esc(r.turma ?? '—')}</td>
            </tr>
            <tr>
              <td><strong>Período:</strong> ${esc(fmtPeriodo(r.periodo_inicio, r.periodo_fim))}</td>
              <td><strong>Status:</strong> ${esc(STATUS_LABEL[r.status] ?? r.status ?? '—')}</td>
            </tr>
            <tr>
              <td><strong>Data de Emissão:</strong> ${esc(fmtData(r.created_at ?? r.data_criacao))}</td>
              <td><strong>Responsável:</strong> ${esc(r.autor_nome ?? _nomeUsuario ?? '—')}</td>
            </tr>
          </table>
          ${secaoPDF('1. Histórico do Caso',          '#4c7adf', r.secao_historico       ?? r.historico      ?? r.conteudo ?? '')}
          ${secaoPDF('2. Intervenções Realizadas',     '#0f9d93', r.secao_intervencoes    ?? r.intervencoes   ?? '')}
          ${secaoPDF('3. Evolução Observada',          '#ed8c2b', r.secao_evolucao        ?? r.evolucao       ?? '')}
          ${secaoPDF('4. Encaminhamentos Realizados',  '#8f63d8', r.secao_encaminhamentos ?? r.encaminhamentos ?? '')}
          ${secaoPDF('5. Recomendações',               '#163a63', r.secao_recomendacoes   ?? r.recomendacoes  ?? '')}
          ${r.observacoes ? secaoPDF('Observações Adicionais', '#5b6f86', r.observacoes) : ''}
          <div style="margin-top:24px;border-top:1px solid #d7e4f2;padding-top:8px;text-align:right;font-size:.75rem;color:#8fa5be;">
            Documento gerado pelo Sistema SAADI — ${agora}
          </div>
        </div>`;

      const area = document.getElementById('areaImpressao');
      if (area) {
        area.innerHTML = html;
        area.style.display = 'block';
        window.print();
        setTimeout(() => {
          area.innerHTML = '';
          area.style.display = 'none';
        }, 1000);
      }
    } catch (err) {
      console.error('[SAADI] Erro ao exportar PDF:', err);
      toast('Erro ao gerar o PDF do relatório.', 'danger');
    }
  }

  function secaoPDF(titulo, cor, texto) {
    if (!texto || !texto.trim()) return '';
    return `
      <div style="margin-bottom:16px;padding:12px 16px;background:#f8fbff;
                  border-left:4px solid ${cor};border-radius:0 8px 8px 0;">
        <p style="font-size:.75rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;
                  color:${cor};margin:0 0 6px;">${esc(titulo)}</p>
        <p style="font-size:.9rem;line-height:1.7;margin:0;white-space:pre-wrap;">${esc(texto)}</p>
      </div>`;
  }

  function inicializarBotaoExportarPDF() {
    document.getElementById('btnExportarPDF')?.addEventListener('click', () => {
      exportarPDF(_relatorioAtualId);
    });
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Excluir relatório
  // ───────────────────────────────────────────────────────────────────────────

  function getModalExclusao() {
    if (!_modalExclusao) {
      const el = document.getElementById('modalConfirmarExclusao');
      if (el) _modalExclusao = new bootstrap.Modal(el);
    }
    return _modalExclusao;
  }

  function confirmarExclusao(id, nomeAluno) {
    document.getElementById('exclusaoRelId').value     = id;
    document.getElementById('exclusaoNomeAluno').textContent = nomeAluno ?? '—';
    getModalExclusao()?.show();
  }

  function inicializarExclusao() {
    document.getElementById('btnConfirmarExclusao')?.addEventListener('click', async () => {
      const id = document.getElementById('exclusaoRelId')?.value;
      if (!id) return;

      const btn = document.getElementById('btnConfirmarExclusao');
      const txt = btn?.textContent;
      try {
        if (btn) { btn.disabled = true; btn.textContent = 'Excluindo…'; }

        const resp = await fetch(`/api/relatorios/${id}`, {
          method: 'DELETE',
          credentials: 'same-origin',
          headers: { Accept: 'application/json' },
        });

        if (!resp.ok) {
          const json = await resp.json().catch(() => ({}));
          toast(json.message || 'Erro ao excluir relatório.', 'danger');
          return;
        }

        getModalExclusao()?.hide();
        toast('Relatório excluído com sucesso.', 'success');
        carregarDashboard();
        carregarRelatorios(_paginaAtual, coletarFiltros());
      } catch (err) {
        console.error('[SAADI] Erro ao excluir relatório:', err);
        toast('Erro de conexão ao excluir relatório.', 'danger');
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = txt; }
      }
    });
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Inicialização geral
  // ───────────────────────────────────────────────────────────────────────────

  function init() {
    preencherPerfil();
    inicializarSair();
    carregarDashboard();
    carregarAlunos();
    carregarRelatorios(1);
    inicializarFiltros();
    inicializarFormNovoRel();
    inicializarResetModalNovoRel();
    inicializarTabelaAcoes();
    inicializarBotaoExportarPDF();
    inicializarExclusao();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
