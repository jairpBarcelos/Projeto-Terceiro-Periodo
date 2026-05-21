/**
 * triagensPsicopedagogo.js
 * Controlador do módulo de Triagens e Avaliações para o Psicopedagogo.
 */

(function () {
  'use strict';

  // -------------------------------------------------------------------------
  // Elementos DOM
  // -------------------------------------------------------------------------
  const nomeUsuarioEl = document.getElementById('nomeUsuario');
  const nomeInstituicaoEl = document.querySelector('.nomeInstituicao');
  const btnSair = document.getElementById('btnSair');

  // Métricas
  const totalTriagensEl = document.getElementById('totalTriagens');
  const totalAguardandoEl = document.getElementById('totalAguardando');
  const totalEmProcessoEl = document.getElementById('totalEmProcesso');
  const totalConcluidasEl = document.getElementById('totalConcluidas');

  // Formulário
  const formTriagem = document.getElementById('formTriagem');
  const selectAluno = document.getElementById('atendimentoAluno');
  const inputData = document.getElementById('atendimentoData');
  const selectTipo = document.getElementById('atendimentoTipo');
  const selectStatus = document.getElementById('atendimentoStatus');
  const textDescricao = document.getElementById('atendimentoDescricao');
  const textEvolucao = document.getElementById('atendimentoEvolucao');
  const textObservacoes = document.getElementById('atendimentoObservacoes');

  // Tabela e Paginação
  const tabelaTriagens = document.getElementById('tabelaTriagens');
  const tabelaBody = tabelaTriagens ? tabelaTriagens.querySelector('tbody') : null;
  const paginacaoEl = document.getElementById('paginacaoTriagens');

  let paginaAtual = 1;
  const limiteItens = 10;

  // -------------------------------------------------------------------------
  // Utils
  // -------------------------------------------------------------------------
  function escapeHTML(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;');
  }

  function formatarData(dataStr) {
    if (!dataStr) return '-';
    try {
      const partes = dataStr.split('T')[0].split('-');
      if (partes.length === 3) {
        return `${partes[2]}/${partes[1]}/${partes[0]}`;
      }
      return dataStr;
    } catch {
      return dataStr;
    }
  }

  function obterBadgeStatus(status) {
    switch (status) {
      case 'aguardando_entrevista':
        return '<span class="badge bg-warning text-dark">Aguardando Entrevista</span>';
      case 'em_processo':
        return '<span class="badge bg-info text-dark">Em Processo</span>';
      case 'concluido':
        return '<span class="badge bg-success">Concluído</span>';
      default:
        return `<span class="badge bg-secondary">${escapeHTML(status)}</span>`;
    }
  }

  function obterTextoTipo(tipo) {
    switch (tipo) {
      case 'triagem':
        return 'Triagem';
      case 'acompanhamento':
        return 'Acompanhamento';
      case 'evolucao':
        return 'Evolução';
      default:
        return escapeHTML(tipo);
    }
  }

  // -------------------------------------------------------------------------
  // Perfil e Autenticação
  // -------------------------------------------------------------------------
  let userUnidadeId = null;

  function preencherPerfil() {
    try {
      const user = JSON.parse(localStorage.getItem('saadi_user_info') || '{}');
      if (user && user.nome) {
        userUnidadeId = user.unidade_id || null;
        if (nomeUsuarioEl) {
          nomeUsuarioEl.textContent = `Bem-vindo(a), ${user.nome.split(' ')[0]}!`;
        }
        if (nomeInstituicaoEl && user.unidade_name) {
          nomeInstituicaoEl.textContent = user.unidade_name;
        }
      }
    } catch (err) {
      console.error('[SAADI] Erro ao carregar informações de perfil:', err);
    }
  }

  function inicializarSair() {
    if (!btnSair) return;
    btnSair.addEventListener('click', async function (e) {
      e.preventDefault();
      try {
        await fetch('/api/auth/logout', {
          method: 'POST',
          credentials: 'same-origin',
        });
      } catch (err) {
        console.warn('[SAADI] Erro ao chamar endpoint de logout:', err);
      } finally {
        if (window.saadiAuth && typeof window.saadiAuth.clearTokens === 'function') {
          window.saadiAuth.clearTokens();
        }
        window.location.href = '/index.html';
      }
    });
  }

  // -------------------------------------------------------------------------
  // Inicializar Data Atual
  // -------------------------------------------------------------------------
  function setarDataPadrao() {
    if (inputData) {
      const hoje = new Date().toISOString().split('T')[0];
      inputData.value = hoje;
    }
  }

  // -------------------------------------------------------------------------
  // Carregamento de Alunos (Tenant Escolar)
  // -------------------------------------------------------------------------
  async function carregarAlunos() {
    if (!selectAluno) return;
    try {
      let url = '/api/alunos?limit=100&status=ativo';
      if (userUnidadeId) {
        url += `&unidade_id=${userUnidadeId}`;
      }

      const resp = await fetch(url, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) throw new Error(`Status: ${resp.status}`);

      const json = await resp.json();
      const alunos = json.data?.items || json.items || [];

      selectAluno.innerHTML = '<option value="">Selecione um aluno...</option>';
      alunos.forEach(aluno => {
        const option = document.createElement('option');
        option.value = aluno.id;
        option.textContent = `${aluno.nome_completo} (RA: ${aluno.ra || '-'})`;
        selectAluno.appendChild(option);
      });
    } catch (err) {
      console.error('[SAADI] Erro ao carregar alunos para triagem:', err);
      selectAluno.innerHTML = '<option value="">Erro ao carregar alunos</option>';
    }
  }

  // -------------------------------------------------------------------------
  // Dashboard / Métricas
  // -------------------------------------------------------------------------
  async function carregarMétricas() {
    try {
      const resp = await fetch('/api/triagens/dashboard', {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) return;

      const json = await resp.json();
      const d = json.data ?? json;

      if (totalTriagensEl) totalTriagensEl.textContent = d.total ?? '0';
      if (totalAguardandoEl) totalAguardandoEl.textContent = d.aguardando ?? '0';
      if (totalEmProcessoEl) totalEmProcessoEl.textContent = d.em_andamento ?? '0';
      if (totalConcluidasEl) totalConcluidasEl.textContent = d.concluidas ?? '0';
    } catch (err) {
      console.error('[SAADI] Erro ao carregar dashboard de triagens:', err);
    }
  }

  // -------------------------------------------------------------------------
  // Histórico de Triagens
  // -------------------------------------------------------------------------
  async function carregarTabelaTriagens(page = 1) {
    if (!tabelaBody) return;
    tabelaBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Carregando histórico...</td></tr>';

    try {
      let url = `/api/triagens?page=${page}&limit=${limiteItens}`;

      const resp = await fetch(url, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) throw new Error(`Status: ${resp.status}`);

      const json = await resp.json();
      const items = json.data?.items || json.items || [];
      const total = json.data?.total || json.total || 0;

      if (items.length === 0) {
        tabelaBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Nenhum atendimento ou triagem registrada.</td></tr>';
        if (paginacaoEl) paginacaoEl.innerHTML = '';
        return;
      }

      tabelaBody.innerHTML = '';
      items.forEach(t => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${escapeHTML(formatarData(t.data_registro))}</strong></td>
          <td>${escapeHTML(t.aluno_nome)}</td>
          <td><span class="badge bg-secondary">${obterTextoTipo(t.tipo_registro)}</span></td>
          <td><div class="text-truncate" style="max-width: 250px;" title="${escapeHTML(t.descricao || '')}">${escapeHTML(t.descricao || '-')}</div></td>
          <td><div class="text-truncate" style="max-width: 250px;" title="${escapeHTML(t.evolucao || '')}">${escapeHTML(t.evolucao || '-')}</div></td>
          <td>${obterBadgeStatus(t.status)}</td>
        `;
        tabelaBody.appendChild(tr);
      });

      paginaAtual = page;
      renderizarPaginacao(total);
    } catch (err) {
      console.error('[SAADI] Erro ao listar triagens:', err);
      tabelaBody.innerHTML = '<tr><td colspan="6" class="text-center text-danger py-4">Falha ao carregar histórico de atendimentos.</td></tr>';
    }
  }

  function renderizarPaginacao(totalItens) {
    if (!paginacaoEl) return;
    const totalPaginas = Math.ceil(totalItens / limiteItens);
    if (totalPaginas <= 1) {
      paginacaoEl.innerHTML = '';
      return;
    }

    let html = '<ul class="pagination pagination-sm m-0">';

    // Anterior
    html += `<li class="page-item ${paginaAtual === 1 ? 'disabled' : ''}">
      <button class="page-link" data-page="${paginaAtual - 1}" type="button">Anterior</button>
    </li>`;

    // Páginas
    for (let i = 1; i <= totalPaginas; i++) {
      html += `<li class="page-item ${paginaAtual === i ? 'active' : ''}">
        <button class="page-link" data-page="${i}" type="button">${i}</button>
      </li>`;
    }

    // Próximo
    html += `<li class="page-item ${paginaAtual === totalPaginas ? 'disabled' : ''}">
      <button class="page-link" data-page="${paginaAtual + 1}" type="button">Próximo</button>
    </li>`;

    html += '</ul>';
    paginacaoEl.innerHTML = html;

    paginacaoEl.querySelectorAll('.page-link').forEach(btn => {
      btn.addEventListener('click', function () {
        const pg = parseInt(this.getAttribute('data-page'), 10);
        if (pg && pg !== paginaAtual) {
          carregarTabelaTriagens(pg);
        }
      });
    });
  }

  // -------------------------------------------------------------------------
  // Submissão do Formulário
  // -------------------------------------------------------------------------
  function inicializarFormulario() {
    if (!formTriagem) return;
    formTriagem.addEventListener('submit', async function (e) {
      e.preventDefault();

      const alunoId = parseInt(selectAluno.value, 10);
      const dataReg = inputData.value;
      const tipo = selectTipo.value;
      const status = selectStatus.value;
      const desc = textDescricao.value.trim();
      const evol = textEvolucao.value.trim();
      const obs = textObservacoes.value.trim();

      if (!alunoId) {
        alert('Por favor, selecione um estudante.');
        return;
      }

      const payload = {
        aluno_id: alunoId,
        data_registro: dataReg,
        tipo_registro: tipo,
        status: status,
        descricao: desc || null,
        evolucao: evol || null,
        observacoes: obs || null,
      };

      try {
        const submitBtn = formTriagem.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.textContent = 'Gravando...';
        }

        const resp = await fetch('/api/triagens', {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify(payload),
        });

        if (!resp.ok) {
          const errData = await resp.json();
          throw new Error(errData.message || 'Erro ao registrar atendimento.');
        }

        alert('Atendimento/Triagem registrado com sucesso!');
        formTriagem.reset();
        setarDataPadrao();
        
        // Recarrega dados atualizados
        await Promise.all([
          carregarMétricas(),
          carregarTabelaTriagens(1)
        ]);

      } catch (err) {
        console.error('[SAADI] Erro ao salvar triagem:', err);
        alert(`Erro: ${err.message}`);
      } finally {
        const submitBtn = formTriagem.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Salvar atendimento';
        }
      }
    });
  }

  // -------------------------------------------------------------------------
  // Inicialização Geral
  // -------------------------------------------------------------------------
  function init() {
    preencherPerfil();
    inicializarSair();
    setarDataPadrao();
    carregarAlunos();
    carregarMétricas();
    carregarTabelaTriagens(1);
    inicializarFormulario();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
