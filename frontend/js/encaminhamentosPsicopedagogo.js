/**
 * encaminhamentosPsicopedagogo.js
 * Controlador completo do módulo de Encaminhamentos para o Psicopedagogo.
 * Cobre: dashboard, listagem, filtros, paginação, criação e registro de retorno.
 */

(function () {
  'use strict';

  // ───────────────────────────────────────────────────────────────────────────
  // Estado global do módulo
  // ───────────────────────────────────────────────────────────────────────────
  let _paginaAtual = 1;
  const LIMITE = 15;

  // Instâncias de modal Bootstrap (inicializadas sob demanda)
  let _modalNovoEnc    = null;
  let _modalRetorno    = null;
  let _modalDetalhes   = null;

  // ───────────────────────────────────────────────────────────────────────────
  // Utilitários
  // ───────────────────────────────────────────────────────────────────────────

  /** Escapa strings contra XSS. */
  function esc(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /** Formata data ISO → dd/mm/aaaa. */
  function fmtData(iso) {
    if (!iso) return '—';
    const d = new Date(iso + (iso.length === 10 ? 'T00:00:00' : ''));
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleDateString('pt-BR');
  }

  /** Preenche textContent de um seletor. */
  function setTexto(sel, val) {
    const el = document.querySelector(sel);
    if (el) el.textContent = val ?? '—';
  }

  /** Exibe toast de feedback no canto superior direito. */
  function toast(msg, tipo = 'success') {
    const el = document.createElement('div');
    el.className = `alert alert-${tipo} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    el.style.cssText = 'z-index:9999;min-width:280px;box-shadow:0 4px 16px rgba(0,0,0,.15)';
    el.innerHTML = `${esc(msg)}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>`;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 5000);
  }

  /** Spinner de carregamento inline para a tabela. */
  function tbodyCarregando(span = 7) {
    return `<tr><td colspan="${span}" class="text-center text-muted py-4">
      <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
      Carregando…</td></tr>`;
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Labels e badges
  // ───────────────────────────────────────────────────────────────────────────

  const TIPO_LABEL = { interno: 'Interno', externo: 'Externo' };

  const STATUS_LABEL = {
    aberto:        'Aguardando',
    em_andamento:  'Em andamento',
    concluido:     'Retorno Recebido',
    sem_retorno:   'Sem Retorno',
    cancelado:     'Cancelado',
  };

  const PRIORIDADE_LABEL = { alta: 'Alta', media: 'Média', baixa: 'Baixa' };

  function badgeTipo(tipo) {
    const cls = tipo === 'externo' ? 'bg-info text-dark' : 'bg-secondary';
    return `<span class="badge ${cls}">${esc(TIPO_LABEL[tipo] ?? tipo)}</span>`;
  }

  function badgeStatus(status) {
    const mapa = {
      aberto:       'bg-warning text-dark',
      em_andamento: 'bg-primary',
      concluido:    'bg-success',
      sem_retorno:  'bg-purple text-white',
      cancelado:    'bg-secondary',
    };
    const cls   = mapa[status] ?? 'bg-light text-dark';
    const label = STATUS_LABEL[status] ?? status;

    // Fallback de cor para "bg-purple" (não nativo do Bootstrap)
    const style = status === 'sem_retorno'
      ? ' style="background:#6f42c1!important;"'
      : '';

    return `<span class="badge ${cls}"${style}>${esc(label)}</span>`;
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Perfil do usuário
  // ───────────────────────────────────────────────────────────────────────────

  let _unidadeId = null;

  function preencherPerfil() {
    try {
      const user = JSON.parse(localStorage.getItem('saadi_user_info') || '{}');
      if (!user) return;
      _unidadeId = user.unidade_id || null;
      const el = document.getElementById('nomeUsuario');
      if (el && user.nome) {
        el.textContent = `Bem-vindo(a), ${user.nome.split(' ')[0]}!`;
      }
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
      try {
        await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
      } catch { /* ok */ } finally {
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
      const resp = await fetch('/api/encaminhamentos/dashboard', {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) return;
      const json = await resp.json();
      const d = json.data ?? json;

      setTexto('#metricaAbertos',    d.abertos      ?? '—');
      setTexto('#metricaInternos',   d.internos     ?? '—');
      setTexto('#metricaExternos',   d.externos     ?? '—');
      setTexto('#metricaComRetorno', d.com_retorno  ?? '—');
      setTexto('#metricaSemRetorno', d.sem_retorno  ?? '—');
    } catch (err) {
      console.error('[SAADI] Dashboard de encaminhamentos:', err);
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Carregamento da lista de alunos (para selects)
  // ───────────────────────────────────────────────────────────────────────────

  async function carregarAlunos() {
    const selects = document.querySelectorAll('#encAluno');
    if (!selects.length) return;

    try {
      let url = '/api/alunos?limit=200&status=ativo';
      if (_unidadeId) url += `&unidade_id=${_unidadeId}`;

      const resp = await fetch(url, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const json  = await resp.json();
      const alunos = json.data?.items ?? json.items ?? [];

      const placeholder = '<option value="">Selecione um aluno…</option>';
      const options = alunos.map(a =>
        `<option value="${esc(a.id)}">${esc(a.nome_completo)} (RA: ${esc(a.ra ?? '-')})</option>`
      ).join('');

      selects.forEach(sel => { sel.innerHTML = placeholder + options; });
    } catch (err) {
      console.error('[SAADI] Erro ao carregar alunos:', err);
      selects.forEach(sel => {
        sel.innerHTML = '<option value="">Erro ao carregar alunos</option>';
      });
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Tabela de encaminhamentos
  // ───────────────────────────────────────────────────────────────────────────

  async function carregarEncaminhamentos(page = 1, filtros = {}) {
    const tbody = document.querySelector('#tabelaEncaminhamentos tbody');
    if (!tbody) return;

    tbody.innerHTML = tbodyCarregando(7);

    const params = new URLSearchParams({ page, limit: LIMITE, ...filtros });

    try {
      const resp = await fetch(`/api/encaminhamentos?${params}`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">
          <strong>Erro:</strong> Não foi possível carregar (HTTP ${resp.status}).</td></tr>`;
        return;
      }

      const json  = await resp.json();
      const items = json.items ?? json.data?.items ?? [];
      const total = json.total ?? json.data?.total ?? 0;

      if (!items.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">
          Nenhum encaminhamento encontrado.</td></tr>`;
        atualizarPaginacao(0, page, LIMITE);
        return;
      }

      tbody.innerHTML = items.map(enc => {
        // Botões de ações
        let acoes = `
          <button class="btn btn-sm btn-outline-primary btn-ver-enc me-1" data-id="${esc(enc.id)}"
            title="Ver detalhes" aria-label="Ver detalhes do encaminhamento">Ver</button>`;

        const podeEditar = enc.status === 'aberto' || enc.status === 'em_andamento';
        if (podeEditar) {
          acoes += `
          <button class="btn btn-sm btn-outline-secondary btn-editar-enc me-1" data-id="${esc(enc.id)}"
            title="Editar" aria-label="Editar encaminhamento">Editar</button>`;
        }

        const podeRetorno = enc.status !== 'cancelado';
        if (podeRetorno) {
          const labelBtn = (enc.status === 'concluido' || enc.status === 'sem_retorno')
            ? 'Ver Retorno'
            : 'Registrar Retorno';
          const clsBtn = (enc.status === 'concluido' || enc.status === 'sem_retorno')
            ? 'btn-outline-secondary'
            : 'btn-success';
          acoes += `
          <button class="btn btn-sm ${clsBtn} btn-dar-retorno" data-id="${esc(enc.id)}"
            title="${esc(labelBtn)}" aria-label="${esc(labelBtn)}">${esc(labelBtn)}</button>`;
        }

        return `
          <tr>
            <td><strong>${esc(enc.aluno_nome ?? '—')}</strong></td>
            <td>${badgeTipo(enc.tipo)}</td>
            <td>${esc(enc.destino ?? '—')}</td>
            <td>${esc(fmtData(enc.created_at ?? enc.data_encaminhamento))}</td>
            <td>${esc(fmtData(enc.prazo_retorno))}</td>
            <td>${badgeStatus(enc.status)}</td>
            <td><div class="d-flex flex-wrap gap-1">${acoes}</div></td>
          </tr>`;
      }).join('');

      _paginaAtual = page;
      atualizarPaginacao(total, page, LIMITE);
    } catch (err) {
      console.error('[SAADI] Erro ao carregar encaminhamentos:', err);
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">
        Erro de conexão com o servidor.</td></tr>`;
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Paginação
  // ───────────────────────────────────────────────────────────────────────────

  function atualizarPaginacao(total, page, limit) {
    const container = document.getElementById('paginacaoEncaminhamentos');
    if (!container) return;

    const totalPaginas = Math.ceil(total / limit) || 1;

    if (totalPaginas <= 1) {
      container.innerHTML = '';
      return;
    }

    const prevDisabled = page <= 1 ? 'disabled' : '';
    const nextDisabled = page >= totalPaginas ? 'disabled' : '';

    container.innerHTML = `
      <nav aria-label="Paginação de encaminhamentos">
        <ul class="pagination pagination-sm mb-0">
          <li class="page-item ${prevDisabled}">
            <button class="page-link" id="encBtnAnterior" aria-label="Página anterior">Anterior</button>
          </li>
          <li class="page-item disabled">
            <span class="page-link">${page} / ${totalPaginas}</span>
          </li>
          <li class="page-item ${nextDisabled}">
            <button class="page-link" id="encBtnProxima" aria-label="Próxima página">Próxima</button>
          </li>
        </ul>
      </nav>`;

    document.getElementById('encBtnAnterior')
      ?.addEventListener('click', () => carregarEncaminhamentos(page - 1, coletarFiltros()));
    document.getElementById('encBtnProxima')
      ?.addEventListener('click', () => carregarEncaminhamentos(page + 1, coletarFiltros()));
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Filtros
  // ───────────────────────────────────────────────────────────────────────────

  function coletarFiltros() {
    const filtros = {};
    const q      = document.getElementById('filtroBuscaEnc')?.value?.trim();
    const tipo   = document.getElementById('filtroTipoEnc')?.value;
    const status = document.getElementById('filtroStatusEnc')?.value;
    if (q)      filtros.q      = q;
    if (tipo)   filtros.tipo   = tipo;
    if (status) filtros.status = status;
    return filtros;
  }

  function inicializarFiltros() {
    const form = document.getElementById('formFiltrosEnc');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        carregarEncaminhamentos(1, coletarFiltros());
      });
    }

    document.getElementById('btnLimparFiltrosEnc')?.addEventListener('click', () => {
      form?.reset();
      carregarEncaminhamentos(1);
    });

    document.getElementById('filtroBuscaEnc')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') carregarEncaminhamentos(1, coletarFiltros());
    });
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Delegação de ações na tabela
  // ───────────────────────────────────────────────────────────────────────────

  function inicializarTabelaAcoes() {
    const tbody = document.querySelector('#tabelaEncaminhamentos tbody');
    if (!tbody) return;

    tbody.addEventListener('click', (e) => {
      const btnVer     = e.target.closest('.btn-ver-enc');
      const btnEditar  = e.target.closest('.btn-editar-enc');
      const btnRetorno = e.target.closest('.btn-dar-retorno');

      if (btnVer)     abrirModalDetalhes(btnVer.dataset.id);
      if (btnEditar)  abrirModalEdicao(btnEditar.dataset.id);
      if (btnRetorno) abrirModalRetorno(btnRetorno.dataset.id);
    });
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Modal: Novo Encaminhamento
  // ───────────────────────────────────────────────────────────────────────────

  function getModalNovoEnc() {
    if (!_modalNovoEnc) {
      const el = document.getElementById('modalNovoEncaminhamento');
      if (el) _modalNovoEnc = new bootstrap.Modal(el);
    }
    return _modalNovoEnc;
  }

  function inicializarFormNovoEnc() {
    const form = document.getElementById('formNovoEnc');
    if (!form) return;

    // Define data atual como padrão
    const hoje = new Date().toISOString().split('T')[0];
    const encData = document.getElementById('encData');
    if (encData) encData.value = hoje;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const alunoId    = document.getElementById('encAluno')?.value;
      const tipo       = document.getElementById('encTipo')?.value;
      const destino    = document.getElementById('encDestino')?.value?.trim();
      const prioridade = document.getElementById('encPrioridade')?.value;
      const data       = document.getElementById('encData')?.value;
      const prazo      = document.getElementById('encPrazoRetorno')?.value || null;
      const motivo     = document.getElementById('encMotivo')?.value?.trim();
      const obs        = document.getElementById('encObservacoes')?.value?.trim() || null;

      if (!alunoId) { toast('Por favor, selecione um aluno.', 'warning'); return; }
      if (!tipo)    { toast('Por favor, selecione o tipo de encaminhamento.', 'warning'); return; }
      if (!destino) { toast('Por favor, informe o destino / serviço.', 'warning'); return; }
      if (!motivo)  { toast('Por favor, descreva o motivo do encaminhamento.', 'warning'); return; }

      const payload = {
        aluno_id:           parseInt(alunoId, 10),
        tipo,
        destino,
        prioridade,
        data_encaminhamento: data || null,
        prazo_retorno:       prazo,
        motivo,
        observacoes:         obs,
        status:              'aberto',
      };

      const btnSalvar = document.getElementById('btnSalvarNovoEnc');
      const txtOriginal = btnSalvar?.textContent;

      try {
        if (btnSalvar) {
          btnSalvar.disabled = true;
          btnSalvar.innerHTML =
            '<span class="spinner-border spinner-border-sm" role="status"></span> Salvando…';
        }

        const resp = await fetch('/api/encaminhamentos', {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify(payload),
        });

        const json = await resp.json();

        if (!resp.ok) {
          toast(json.message || 'Erro ao salvar encaminhamento.', 'danger');
          return;
        }

        getModalNovoEnc()?.hide();
        form.reset();

        // Restaura data padrão após reset
        if (encData) encData.value = new Date().toISOString().split('T')[0];

        toast('Encaminhamento registrado com sucesso!', 'success');
        carregarDashboard();
        carregarEncaminhamentos(_paginaAtual, coletarFiltros());

      } catch (err) {
        console.error('[SAADI] Erro ao criar encaminhamento:', err);
        toast('Erro de conexão ao salvar encaminhamento.', 'danger');
      } finally {
        if (btnSalvar) {
          btnSalvar.disabled = false;
          btnSalvar.textContent = txtOriginal;
        }
      }
    });
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Modal: Detalhes (somente leitura)
  // ───────────────────────────────────────────────────────────────────────────

  function getModalDetalhes() {
    if (!_modalDetalhes) {
      const el = document.getElementById('modalVerDetalhes');
      if (el) _modalDetalhes = new bootstrap.Modal(el);
    }
    return _modalDetalhes;
  }

  async function abrirModalDetalhes(id) {
    const modal = getModalDetalhes();
    if (!modal) return;
    const corpo = document.getElementById('corpoModalDetalhes');
    if (corpo) corpo.innerHTML = '<p class="text-center text-muted py-3">Carregando…</p>';
    modal.show();

    try {
      const resp = await fetch(`/api/encaminhamentos/${id}`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) {
        if (corpo) corpo.innerHTML = `<p class="text-danger">Erro ao carregar detalhes (HTTP ${resp.status}).</p>`;
        return;
      }
      const json = await resp.json();
      const enc  = json.item ?? json.data?.item ?? json;

      if (corpo) {
        corpo.innerHTML = `
          <div class="row g-3">
            <div class="col-sm-6">
              <p class="mb-1 text-muted" style="font-size:.82rem;">ALUNO</p>
              <p class="fw-bold mb-0">${esc(enc.aluno_nome ?? '—')}</p>
            </div>
            <div class="col-sm-6">
              <p class="mb-1 text-muted" style="font-size:.82rem;">TIPO</p>
              <p class="mb-0">${badgeTipo(enc.tipo)}</p>
            </div>
            <div class="col-sm-6">
              <p class="mb-1 text-muted" style="font-size:.82rem;">DESTINO / SERVIÇO</p>
              <p class="fw-bold mb-0">${esc(enc.destino ?? '—')}</p>
            </div>
            <div class="col-sm-6">
              <p class="mb-1 text-muted" style="font-size:.82rem;">STATUS</p>
              <p class="mb-0">${badgeStatus(enc.status)}</p>
            </div>
            <div class="col-sm-6">
              <p class="mb-1 text-muted" style="font-size:.82rem;">DATA DO ENCAMINHAMENTO</p>
              <p class="mb-0">${esc(fmtData(enc.created_at ?? enc.data_encaminhamento))}</p>
            </div>
            <div class="col-sm-6">
              <p class="mb-1 text-muted" style="font-size:.82rem;">PRAZO DE RETORNO</p>
              <p class="mb-0">${esc(fmtData(enc.prazo_retorno))}</p>
            </div>
            ${enc.prioridade ? `
            <div class="col-sm-6">
              <p class="mb-1 text-muted" style="font-size:.82rem;">PRIORIDADE</p>
              <p class="mb-0">${esc(PRIORIDADE_LABEL[enc.prioridade] ?? enc.prioridade)}</p>
            </div>` : ''}
            <div class="col-12">
              <p class="mb-1 text-muted" style="font-size:.82rem;">MOTIVO</p>
              <div class="p-3 bg-light border rounded" style="white-space:pre-wrap">${esc(enc.motivo ?? '—')}</div>
            </div>
            ${enc.observacoes ? `
            <div class="col-12">
              <p class="mb-1 text-muted" style="font-size:.82rem;">OBSERVAÇÕES</p>
              <div class="p-3 bg-light border rounded" style="white-space:pre-wrap">${esc(enc.observacoes)}</div>
            </div>` : ''}
            ${enc.observacao_retorno ? `
            <div class="col-12">
              <hr>
              <p class="mb-1 text-muted" style="font-size:.82rem;">PARECER DE RETORNO</p>
              <div class="p-3 border rounded" style="background:#f0f9f0;white-space:pre-wrap">${esc(enc.observacao_retorno)}</div>
            </div>` : ''}
          </div>`;
      }
    } catch (err) {
      console.error('[SAADI] Erro ao abrir detalhes:', err);
      if (corpo) corpo.innerHTML = '<p class="text-danger">Erro de conexão.</p>';
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Modal: Editar (abre o modal de novo enc com dados preenchidos)
  // ───────────────────────────────────────────────────────────────────────────

  async function abrirModalEdicao(id) {
    try {
      const resp = await fetch(`/api/encaminhamentos/${id}`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) { toast('Não foi possível carregar os dados para edição.', 'danger'); return; }

      const json = await resp.json();
      const enc  = json.item ?? json.data?.item ?? json;

      // Preenche os campos do formulário de novo enc
      const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val ?? ''; };
      setVal('encAluno',        enc.aluno_id);
      setVal('encTipo',         enc.tipo);
      setVal('encDestino',      enc.destino);
      setVal('encPrioridade',   enc.prioridade ?? 'media');
      setVal('encData',         (enc.data_encaminhamento ?? enc.created_at ?? '').substring(0, 10));
      setVal('encPrazoRetorno', (enc.prazo_retorno ?? '').substring(0, 10));
      setVal('encMotivo',       enc.motivo);
      setVal('encObservacoes',  enc.observacoes);

      // Guarda o id para o submit saber que é edição
      const form = document.getElementById('formNovoEnc');
      if (form) form.dataset.editId = id;

      // Muda título do modal
      const titulo = document.getElementById('modalNovoEncTitulo');
      if (titulo) titulo.textContent = 'Editar Encaminhamento';

      getModalNovoEnc()?.show();
    } catch (err) {
      console.error('[SAADI] Erro ao abrir edição:', err);
      toast('Erro de conexão ao carregar encaminhamento.', 'danger');
    }
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Modal: Registrar Retorno
  // ───────────────────────────────────────────────────────────────────────────

  function getModalRetorno() {
    if (!_modalRetorno) {
      const el = document.getElementById('modalDarRetorno');
      if (el) _modalRetorno = new bootstrap.Modal(el);
    }
    return _modalRetorno;
  }

  async function abrirModalRetorno(id) {
    const modal = getModalRetorno();
    if (!modal) return;

    try {
      const resp = await fetch(`/api/encaminhamentos/${id}`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) { toast('Não foi possível carregar os dados do encaminhamento.', 'danger'); return; }

      const json = await resp.json();
      const enc  = json.item ?? json.data?.item ?? json;
      if (!enc)  { toast('Dados do encaminhamento não encontrados.', 'danger'); return; }

      // Preenche cabeçalho informativo
      setTexto('#retornoAluno',   enc.aluno_nome);
      setTexto('#retornoDestino', enc.destino);
      setTexto('#retornoTipo',    TIPO_LABEL[enc.tipo] ?? enc.tipo);

      const encId    = document.getElementById('retornoEncId');
      const campoData   = document.getElementById('campoDataRetorno');
      const campoStatus = document.getElementById('campoStatusRetorno');
      const campoObs    = document.getElementById('campoObservacaoRetorno');
      const titulo      = document.getElementById('modalDarRetornoTitulo');
      const btnSubmit   = document.getElementById('btnSubmitRetorno');

      if (encId) encId.value = enc.id;

      const jaSobStatus = enc.status === 'concluido' || enc.status === 'sem_retorno' || enc.status === 'cancelado';

      if (titulo)  titulo.textContent  = jaSobStatus ? 'Visualizar Retorno' : 'Registrar Retorno';
      if (btnSubmit) btnSubmit.style.display = jaSobStatus ? 'none' : 'block';

      const soLeitura = jaSobStatus && Boolean(enc.observacao_retorno);

      if (campoData) {
        campoData.value    = (enc.data_retorno ?? new Date().toISOString()).substring(0, 10);
        campoData.disabled = soLeitura;
      }
      if (campoStatus) {
        campoStatus.value    = enc.status === 'aberto' ? 'concluido' : enc.status;
        campoStatus.disabled = soLeitura;
      }
      if (campoObs) {
        campoObs.value    = enc.observacao_retorno ?? '';
        campoObs.disabled = soLeitura;
      }

      modal.show();
    } catch (err) {
      console.error('[SAADI] Erro ao abrir modal de retorno:', err);
      toast('Erro de conexão ao carregar encaminhamento.', 'danger');
    }
  }

  function inicializarFormularioRetorno() {
    const form = document.getElementById('formDarRetorno');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const id       = document.getElementById('retornoEncId')?.value;
      const data     = document.getElementById('campoDataRetorno')?.value;
      const status   = document.getElementById('campoStatusRetorno')?.value;
      const obs      = document.getElementById('campoObservacaoRetorno')?.value?.trim();

      if (!id || !data || !status || !obs) {
        toast('Preencha todos os campos obrigatórios.', 'warning');
        return;
      }

      const btnSubmit  = document.getElementById('btnSubmitRetorno');
      const txtOriginal = btnSubmit?.textContent;

      try {
        if (btnSubmit) {
          btnSubmit.disabled = true;
          btnSubmit.innerHTML =
            '<span class="spinner-border spinner-border-sm" role="status"></span> Registrando…';
        }

        const resp = await fetch(`/api/encaminhamentos/${id}/retorno`, {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify({ data_retorno: data, status, observacao_retorno: obs }),
        });

        const json = await resp.json();
        if (!resp.ok) { toast(json.message || 'Erro ao registrar retorno.', 'danger'); return; }

        getModalRetorno()?.hide();
        toast('Retorno registrado com sucesso!', 'success');
        carregarDashboard();
        carregarEncaminhamentos(_paginaAtual, coletarFiltros());

      } catch (err) {
        console.error('[SAADI] Erro ao registrar retorno:', err);
        toast('Erro de conexão ao salvar retorno.', 'danger');
      } finally {
        if (btnSubmit) {
          btnSubmit.disabled = false;
          btnSubmit.textContent = txtOriginal;
        }
      }
    });
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Reset do modal de novo enc ao fechar
  // ───────────────────────────────────────────────────────────────────────────

  function inicializarResetModal() {
    const elModal = document.getElementById('modalNovoEncaminhamento');
    if (!elModal) return;

    elModal.addEventListener('hidden.bs.modal', () => {
      const form = document.getElementById('formNovoEnc');
      if (form) {
        form.reset();
        delete form.dataset.editId;
        const encData = document.getElementById('encData');
        if (encData) encData.value = new Date().toISOString().split('T')[0];
      }
      const titulo = document.getElementById('modalNovoEncTitulo');
      if (titulo) titulo.textContent = 'Novo Encaminhamento';
    });
  }

  // ───────────────────────────────────────────────────────────────────────────
  // Inicialização
  // ───────────────────────────────────────────────────────────────────────────

  function init() {
    preencherPerfil();
    inicializarSair();
    carregarDashboard();
    carregarAlunos();
    carregarEncaminhamentos(1);
    inicializarFiltros();
    inicializarFormNovoEnc();
    inicializarFormularioRetorno();
    inicializarTabelaAcoes();
    inicializarResetModal();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
