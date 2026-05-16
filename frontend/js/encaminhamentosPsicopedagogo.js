/**
 * encaminhamentosPsicopedagogo.js
 * Integração frontend → API para o módulo de Encaminhamentos do Psicopedagogo.
 */

(function () {
  'use strict';

  // -------------------------------------------------------------------------
  // Utilitários
  // -------------------------------------------------------------------------

  /** Formata uma data ISO para dd/mm/aaaa. */
  function formatarData(isoString) {
    if (!isoString) return '—';
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleDateString('pt-BR');
  }

  /** Preenche um elemento com texto, protegendo contra XSS. */
  function setTexto(seletor, valor) {
    const el = document.querySelector(seletor);
    if (el) el.textContent = valor ?? '—';
  }

  /** Exibe uma linha de erro dentro de um container. */
  function mostrarErro(container, msg) {
    container.innerHTML = `
      <tr><td colspan="5" class="text-center text-danger py-4">
        <strong>Erro:</strong> ${msg}
      </td></tr>`;
  }

  /** Exibe estado vazio na tabela. */
  function mostrarVazio(tbody) {
    tbody.innerHTML = `
      <tr><td colspan="5" class="text-center text-muted py-4">
        Nenhum encaminhamento encontrado.
      </td></tr>`;
  }

  // -------------------------------------------------------------------------
  // Mapeamento de labels
  // -------------------------------------------------------------------------

  const TIPO_LABEL = { interno: 'Interno', externo: 'Externo' };
  const STATUS_LABEL = {
    aberto: 'Aberto',
    concluido: 'Concluído',
    cancelado: 'Cancelado',
    em_andamento: 'Em andamento',
  };
  const PRIORIDADE_LABEL = { alta: 'Alta', media: 'Média', baixa: 'Baixa' };

  function badgeStatus(status) {
    const mapa = {
      aberto: 'bg-warning text-dark',
      concluido: 'bg-success',
      cancelado: 'bg-secondary',
      em_andamento: 'bg-primary',
    };
    const cls = mapa[status] || 'bg-light text-dark';
    const label = STATUS_LABEL[status] || status;
    return `<span class="badge ${cls}">${label}</span>`;
  }

  // -------------------------------------------------------------------------
  // Dashboard — métricas
  // -------------------------------------------------------------------------

  async function carregarDashboard() {
    try {
      const resp = await fetch('/api/encaminhamentos/dashboard', {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) {
        console.warn('[SAADI] Dashboard de encaminhamentos indisponível:', resp.status);
        return;
      }

      const json = await resp.json();
      const d = json.data ?? json;

      setTexto('#metricaAbertos', d.abertos ?? '—');
      setTexto('#metricaInternos', d.internos ?? '—');
      setTexto('#metricaExternos', d.externos ?? '—');
      setTexto('#metricaComRetorno', d.com_retorno ?? '—');
      setTexto('#metricaSemRetorno', d.sem_retorno ?? '—');
    } catch (err) {
      console.error('[SAADI] Erro ao carregar dashboard:', err);
    }
  }

  // -------------------------------------------------------------------------
  // Tabela de encaminhamentos
  // -------------------------------------------------------------------------

  async function carregarEncaminhamentos(page = 1, filtros = {}) {
    const tbody = document.querySelector('#tabelaEncaminhamentos tbody');
    if (!tbody) return;

    tbody.innerHTML = `
      <tr><td colspan="5" class="text-center text-muted py-4">
        <span class="spinner-border spinner-border-sm" role="status"></span>
        Carregando…
      </td></tr>`;

    const params = new URLSearchParams({ page, limit: 15, ...filtros });

    try {
      const resp = await fetch(`/api/encaminhamentos?${params}`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) {
        mostrarErro(tbody, `Não foi possível carregar os encaminhamentos (HTTP ${resp.status}).`);
        return;
      }

      const json = await resp.json();
      const items = json.items ?? json.data?.items ?? [];
      const total = json.total ?? json.data?.total ?? 0;

      if (items.length === 0) {
        mostrarVazio(tbody);
        atualizarPaginacao(0, page, 15);
        return;
      }

      tbody.innerHTML = items.map((enc) => `
        <tr>
          <td>${formatarData(enc.created_at)}</td>
          <td>${enc.aluno_nome ?? '—'}</td>
          <td>${enc.destino ?? '—'}</td>
          <td><span class="badge ${enc.tipo === 'externo' ? 'bg-info text-dark' : 'bg-secondary'}">${TIPO_LABEL[enc.tipo] ?? enc.tipo}</span></td>
          <td>${badgeStatus(enc.status)}</td>
        </tr>
      `).join('');

      atualizarPaginacao(total, page, 15);
    } catch (err) {
      mostrarErro(tbody, 'Erro de conexão com o servidor.');
      console.error('[SAADI] Erro ao carregar encaminhamentos:', err);
    }
  }

  // -------------------------------------------------------------------------
  // Paginação simples
  // -------------------------------------------------------------------------

  let _paginaAtual = 1;

  function atualizarPaginacao(total, page, limit) {
    const container = document.querySelector('#paginacaoEncaminhamentos');
    if (!container) return;

    const totalPaginas = Math.ceil(total / limit) || 1;
    _paginaAtual = page;

    const prevDisabled = page <= 1 ? 'disabled' : '';
    const nextDisabled = page >= totalPaginas ? 'disabled' : '';

    container.innerHTML = `
      <nav aria-label="Paginação de encaminhamentos">
        <ul class="pagination pagination-sm mb-0">
          <li class="page-item ${prevDisabled}">
            <button class="page-link" id="btnAnterior" aria-label="Página anterior">Anterior</button>
          </li>
          <li class="page-item disabled">
            <span class="page-link">${page} / ${totalPaginas}</span>
          </li>
          <li class="page-item ${nextDisabled}">
            <button class="page-link" id="btnProxima" aria-label="Próxima página">Próxima</button>
          </li>
        </ul>
      </nav>`;

    const btnPrev = document.getElementById('btnAnterior');
    const btnNext = document.getElementById('btnProxima');

    if (btnPrev) btnPrev.addEventListener('click', () => carregarEncaminhamentos(page - 1, coletarFiltros()));
    if (btnNext) btnNext.addEventListener('click', () => carregarEncaminhamentos(page + 1, coletarFiltros()));
  }

  // -------------------------------------------------------------------------
  // Filtros
  // -------------------------------------------------------------------------

  function coletarFiltros() {
    const filtros = {};
    const tipo = document.querySelector('#filtroTipo')?.value;
    const status = document.querySelector('#filtroStatus')?.value;
    const q = document.querySelector('#filtroBusca')?.value?.trim();
    if (tipo) filtros.tipo = tipo;
    if (status) filtros.status = status;
    if (q) filtros.q = q;
    return filtros;
  }

  function inicializarFiltros() {
    const btnFiltrar = document.getElementById('btnFiltrar');
    if (btnFiltrar) {
      btnFiltrar.addEventListener('click', () => carregarEncaminhamentos(1, coletarFiltros()));
    }

    const busca = document.getElementById('filtroBusca');
    if (busca) {
      busca.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') carregarEncaminhamentos(1, coletarFiltros());
      });
    }
  }

  // -------------------------------------------------------------------------
  // Perfil do usuário (reutiliza dado salvo pelo apiClient)
  // -------------------------------------------------------------------------

  function preencherPerfil() {
    try {
      const user = JSON.parse(localStorage.getItem('saadi_user_info') || '{}');
      if (!user) return;

      const nomeEl = document.querySelector('.Perfil p');
      if (nomeEl && user.nome) {
        nomeEl.textContent = `Bem-vindo(a), ${user.nome.split(' ')[0]}!`;
      }
    } catch {
      // silencioso
    }
  }

  // -------------------------------------------------------------------------
  // Inicialização
  // -------------------------------------------------------------------------

  function init() {
    preencherPerfil();
    carregarDashboard();
    carregarEncaminhamentos(1);
    inicializarFiltros();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
