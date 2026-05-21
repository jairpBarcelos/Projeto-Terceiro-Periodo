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

  /** Escapa strings contra XSS. */
  function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#039;');
  }

  /** Exibe uma linha de erro dentro de um container. */
  function mostrarErro(container, msg) {
    container.innerHTML = `
      <tr><td colspan="6" class="text-center text-danger py-4">
        <strong>Erro:</strong> ${msg}
      </td></tr>`;
  }

  /** Exibe estado vazio na tabela. */
  function mostrarVazio(tbody) {
    tbody.innerHTML = `
      <tr><td colspan="6" class="text-center text-muted py-4">
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
    return `<span class="badge ${cls}">${escapeHTML(label)}</span>`;
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
      <tr><td colspan="6" class="text-center text-muted py-4">
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

      tbody.innerHTML = items.map((enc) => {
        let acaoBtn = '';
        if (enc.status === 'concluido' || enc.status === 'cancelado' || enc.data_retorno) {
          acaoBtn = `<button class="btn btn-sm btn-outline-secondary btn-ver-retorno" data-id="${enc.id}">Ver Retorno</button>`;
        } else {
          acaoBtn = `<button class="btn btn-sm btn-primary btn-dar-retorno" data-id="${enc.id}">Dar Retorno</button>`;
        }

        return `
          <tr>
            <td>${escapeHTML(formatarData(enc.created_at))}</td>
            <td>${escapeHTML(enc.aluno_nome ?? '—')}</td>
            <td>${escapeHTML(enc.destino ?? '—')}</td>
            <td><span class="badge ${enc.tipo === 'externo' ? 'bg-info text-dark' : 'bg-secondary'}">${escapeHTML(TIPO_LABEL[enc.tipo] ?? enc.tipo)}</span></td>
            <td>${badgeStatus(enc.status)}</td>
            <td>${acaoBtn}</td>
          </tr>
        `;
      }).join('');

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
  // Modal de Retorno de Encaminhamentos
  // -------------------------------------------------------------------------

  let modalRetornoInstance = null;

  function obterModalRetorno() {
    if (!modalRetornoInstance) {
      const el = document.getElementById('modalDarRetorno');
      if (el) {
        modalRetornoInstance = new bootstrap.Modal(el);
      }
    }
    return modalRetornoInstance;
  }

  async function abrirModalRetorno(id, modoVisualizar = false) {
    const modal = obterModalRetorno();
    if (!modal) return;

    try {
      const resp = await fetch(`/api/encaminhamentos/${id}`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) {
        alert('Não foi possível carregar os detalhes do encaminhamento.');
        return;
      }

      const json = await resp.json();
      const enc = json.item ?? json.data?.item;
      if (!enc) {
        alert('Dados do encaminhamento não encontrados.');
        return;
      }

      // Preenche os campos informativos do modal
      setTexto('#retornoAluno', enc.aluno_nome);
      setTexto('#retornoDestino', enc.destino);
      setTexto('#retornoTipo', TIPO_LABEL[enc.tipo] ?? enc.tipo);
      
      const inputId = document.getElementById('retornoEncId');
      if (inputId) inputId.value = enc.id;

      const campoData = document.getElementById('campoDataRetorno');
      const campoStatus = document.getElementById('campoStatusRetorno');
      const campoObs = document.getElementById('campoObservacaoRetorno');
      const btnSubmit = document.querySelector('#formDarRetorno button[type="submit"]');
      const tituloModal = document.getElementById('modalDarRetornoTitulo');

      if (modoVisualizar) {
        if (tituloModal) tituloModal.textContent = 'Visualizar Retorno de Encaminhamento';
        if (campoData) {
          campoData.value = enc.data_retorno ? enc.data_retorno.substring(0, 10) : '';
          campoData.disabled = true;
        }
        if (campoStatus) {
          campoStatus.value = enc.status || 'concluido';
          campoStatus.disabled = true;
        }
        if (campoObs) {
          campoObs.value = enc.observacao_retorno || 'Nenhuma observação registrada.';
          campoObs.disabled = true;
        }
        if (btnSubmit) btnSubmit.style.display = 'none';
      } else {
        if (tituloModal) tituloModal.textContent = 'Registrar Retorno de Encaminhamento';
        if (campoData) {
          campoData.value = enc.data_retorno ? enc.data_retorno.substring(0, 10) : new Date().toISOString().substring(0, 10);
          campoData.disabled = false;
        }
        if (campoStatus) {
          campoStatus.value = enc.status === 'aberto' ? 'concluido' : enc.status;
          campoStatus.disabled = false;
        }
        if (campoObs) {
          campoObs.value = enc.observacao_retorno || '';
          campoObs.disabled = false;
        }
        if (btnSubmit) btnSubmit.style.display = 'block';
      }

      modal.show();
    } catch (err) {
      console.error('[SAADI] Erro ao abrir modal de retorno:', err);
      alert('Erro de conexão ao carregar dados do encaminhamento.');
    }
  }

  function inicializarFormularioRetorno() {
    const form = document.getElementById('formDarRetorno');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const id = document.getElementById('retornoEncId')?.value;
      const data_retorno = document.getElementById('campoDataRetorno')?.value;
      const status = document.getElementById('campoStatusRetorno')?.value;
      const observacao_retorno = document.getElementById('campoObservacaoRetorno')?.value;

      if (!id || !data_retorno || !status || !observacao_retorno) {
        alert('Por favor, preencha todos os campos obrigatórios.');
        return;
      }

      const btnSubmit = form.querySelector('button[type="submit"]');
      const originalText = btnSubmit ? btnSubmit.textContent : 'Registrar Retorno';

      if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Registrando…';
      }

      try {
        const resp = await fetch(`/api/encaminhamentos/${id}/retorno`, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify({
            data_retorno,
            status,
            observacao_retorno,
          }),
        });

        const json = await resp.json();

        if (!resp.ok) {
          alert(json.message || 'Erro ao registrar retorno de encaminhamento.');
          return;
        }

        // Sucesso
        const modal = obterModalRetorno();
        if (modal) modal.hide();

        // Recarrega dashboard e listagem
        carregarDashboard();
        carregarEncaminhamentos(_paginaAtual, coletarFiltros());

        // Mensagem de sucesso flutuante
        const alertEl = document.createElement('div');
        alertEl.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 end-0 m-3 z-3';
        alertEl.style.zIndex = '9999';
        alertEl.innerHTML = `
          <strong>Sucesso!</strong> Retorno registrado com sucesso.
          <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(alertEl);
        setTimeout(() => alertEl.remove(), 4000);

      } catch (err) {
        console.error('[SAADI] Erro ao registrar retorno:', err);
        alert('Erro de conexão ao salvar retorno.');
      } finally {
        if (btnSubmit) {
          btnSubmit.disabled = false;
          btnSubmit.textContent = originalText;
        }
      }
    });
  }

  function inicializarTabelaAcoes() {
    const tbody = document.querySelector('#tabelaEncaminhamentos tbody');
    if (!tbody) return;

    tbody.addEventListener('click', (e) => {
      const btnDar = e.target.closest('.btn-dar-retorno');
      const btnVer = e.target.closest('.btn-ver-retorno');

      if (btnDar) {
        const id = btnDar.getAttribute('data-id');
        abrirModalRetorno(id, false);
      } else if (btnVer) {
        const id = btnVer.getAttribute('data-id');
        abrirModalRetorno(id, true);
      }
    });
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
    inicializarFormularioRetorno();
    inicializarTabelaAcoes();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
