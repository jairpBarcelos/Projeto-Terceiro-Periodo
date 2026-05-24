/**
 * planosPsicopedagogo.js
 * Controlador do módulo de Planos de Acompanhamento para o Psicopedagogo.
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
  const totalPlanosEl = document.getElementById('totalPlanos');
  const totalPlanosAtivosEl = document.getElementById('totalPlanosAtivos');
  const totalPlanosConcluidosEl = document.getElementById('totalPlanosConcluidos');
  const totalPlanosSuspensosEl = document.getElementById('totalPlanosSuspensos');

  // Formulário
  const formPlano = document.getElementById('formPlano');
  const selectAluno = document.getElementById('planoAluno');
  const inputTitulo = document.getElementById('planoTitulo');
  const inputDataInicio = document.getElementById('planoDataInicio');
  const inputDataFim = document.getElementById('planoDataFim');
  const selectPeriodicidade = document.getElementById('planoPeriodicidade');
  const selectStatus = document.getElementById('planoStatus');
  const textObjetivo = document.getElementById('planoObjetivo');
  const textEstrategias = document.getElementById('planoEstrategias');

  // Tabela e Paginação
  const tabelaPlanos = document.getElementById('tabelaPlanos');
  const tabelaBody = tabelaPlanos ? tabelaPlanos.querySelector('tbody') : null;
  const paginacaoEl = document.getElementById('paginacaoPlanos');

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
      case 'ativo':
        return '<span class="badge bg-success">Ativo</span>';
      case 'concluido':
        return '<span class="badge bg-primary">Concluído</span>';
      case 'suspenso':
        return '<span class="badge bg-danger">Suspenso</span>';
      default:
        return `<span class="badge bg-secondary">${escapeHTML(status)}</span>`;
    }
  }

  function obterTextoPeriodicidade(periodicidade) {
    if (!periodicidade) return '-';
    switch (periodicidade) {
      case 'semanal':
        return 'Semanal';
      case 'quinzenal':
        return 'Quinzenal';
      case 'mensal':
        return 'Mensal';
      case 'outra':
        return 'Outra';
      default:
        return escapeHTML(periodicidade);
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
  // Inicializar Datas Padrão (Hoje e + 6 Meses)
  // -------------------------------------------------------------------------
  function setarDatasPadrao() {
    const hoje = new Date();
    if (inputDataInicio) {
      inputDataInicio.value = hoje.toISOString().split('T')[0];
    }
    if (inputDataFim) {
      const dataFim = new Date();
      dataFim.setMonth(hoje.getMonth() + 6);
      inputDataFim.value = dataFim.toISOString().split('T')[0];
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
      console.error('[SAADI] Erro ao carregar alunos para plano:', err);
      selectAluno.innerHTML = '<option value="">Erro ao carregar alunos</option>';
    }
  }

  // -------------------------------------------------------------------------
  // Dashboard / Métricas
  // -------------------------------------------------------------------------
  async function carregarMétricas() {
    try {
      const resp = await fetch('/api/planos/dashboard', {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) return;

      const json = await resp.json();
      const d = json.data ?? json;

      if (totalPlanosEl) totalPlanosEl.textContent = d.total ?? '0';
      if (totalPlanosAtivosEl) totalPlanosAtivosEl.textContent = d.ativos ?? '0';
      if (totalPlanosConcluidosEl) totalPlanosConcluidosEl.textContent = d.concluidos ?? '0';
      if (totalPlanosSuspensosEl) totalPlanosSuspensosEl.textContent = d.suspensos ?? '0';
    } catch (err) {
      console.error('[SAADI] Erro ao carregar dashboard de planos:', err);
    }
  }

  // -------------------------------------------------------------------------
  // Histórico de Planos
  // -------------------------------------------------------------------------
  async function carregarTabelaPlanos(page = 1) {
    if (!tabelaBody) return;
    tabelaBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Carregando planos...</td></tr>';

    try {
      let url = `/api/planos?page=${page}&limit=${limiteItens}`;

      const resp = await fetch(url, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) throw new Error(`Status: ${resp.status}`);

      const json = await resp.json();
      const items = json.data?.items || json.items || [];
      const total = json.data?.total || json.total || 0;

      if (items.length === 0) {
        tabelaBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Nenhum plano de acompanhamento cadastrado.</td></tr>';
        if (paginacaoEl) paginacaoEl.innerHTML = '';
        return;
      }

      tabelaBody.innerHTML = '';
      items.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${escapeHTML(formatarData(p.data_inicio))}</strong></td>
          <td>${escapeHTML(p.aluno_nome)}</td>
          <td>${escapeHTML(p.titulo)}</td>
          <td><div class="text-truncate" style="max-width: 300px;" title="${escapeHTML(p.objetivo_geral || '')}">${escapeHTML(p.objetivo_geral || '-')}</div></td>
          <td>${obterTextoPeriodicidade(p.periodicidade)}</td>
          <td>${obterBadgeStatus(p.status)}</td>
        `;
        tabelaBody.appendChild(tr);
      });

      paginaAtual = page;
      renderizarPaginacao(total);
    } catch (err) {
      console.error('[SAADI] Erro ao listar planos:', err);
      tabelaBody.innerHTML = '<tr><td colspan="6" class="text-center text-danger py-4">Falha ao carregar planos de acompanhamento.</td></tr>';
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
          carregarTabelaPlanos(pg);
        }
      });
    });
  }

  // -------------------------------------------------------------------------
  // Submissão do Formulário
  // -------------------------------------------------------------------------
  function inicializarFormulario() {
    if (!formPlano) return;
    formPlano.addEventListener('submit', async function (e) {
      e.preventDefault();

      const alunoId = parseInt(selectAluno.value, 10);
      const titulo = inputTitulo.value.trim();
      const dataInicio = inputDataInicio.value;
      const dataFim = inputDataFim.value;
      const periodicidade = selectPeriodicidade.value;
      const status = selectStatus.value;
      const objetivo = textObjetivo.value.trim();
      const estrategias = textEstrategias.value.trim();

      if (!alunoId) {
        alert('Por favor, selecione um estudante.');
        return;
      }

      if (!titulo) {
        alert('Por favor, preencha o título do plano.');
        return;
      }

      const payload = {
        aluno_id: alunoId,
        titulo: titulo,
        data_inicio: dataInicio || null,
        data_fim_prevista: dataFim || null,
        periodicidade: periodicidade,
        status: status,
        objetivo_geral: objetivo || null,
        estrategias: estrategias || null,
      };

      try {
        const submitBtn = formPlano.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.textContent = 'Gravando...';
        }

        const resp = await fetch('/api/planos', {
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
          throw new Error(errData.message || 'Erro ao criar plano de acompanhamento.');
        }

        alert('Plano de acompanhamento cadastrado com sucesso!');
        formPlano.reset();
        setarDatasPadrao();

        // Recarrega dados atualizados
        await Promise.all([
          carregarMétricas(),
          carregarTabelaPlanos(1)
        ]);

      } catch (err) {
        console.error('[SAADI] Erro ao salvar plano:', err);
        alert(`Erro: ${err.message}`);
      } finally {
        const submitBtn = formPlano.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Salvar plano';
        }
      }
    });
  }

  // -------------------------------------------------------------------------
  // Filtros (Mock frontend)
  // -------------------------------------------------------------------------
  function aplicarFiltros() {
    const termoBusca = (document.getElementById('filtroBuscaAluno')?.value || '').toLowerCase();
    const status = (document.getElementById('filtroStatus')?.value || '').toLowerCase();
    const responsavel = (document.getElementById('filtroResponsavel')?.value || '').toLowerCase();
    const frequencia = (document.getElementById('filtroFrequencia')?.value || '').toLowerCase();

    const linhas = document.querySelectorAll('#tabelaPlanos tbody tr');

    linhas.forEach(linha => {
      // Ignorar linha de "carregando" ou "vazio"
      const primeiraCelula = linha.querySelector('td');
      if (primeiraCelula && primeiraCelula.colSpan >= 6) return;

      const nomeAluno = linha.children[1]?.textContent.toLowerCase() || '';
      const periodicidade = linha.children[4]?.textContent.toLowerCase() || '';
      const badgeStatus = linha.children[5]?.textContent.toLowerCase() || '';

      let mostrar = true;

      // Filtro de busca (tempo real)
      if (termoBusca && !nomeAluno.includes(termoBusca)) mostrar = false;
      
      // Filtro de status
      if (status) {
        if (status === 'ativo' && !badgeStatus.includes('ativo')) mostrar = false;
        if (status === 'concluido' && !badgeStatus.includes('concluído')) mostrar = false;
        if (status === 'suspenso' && !badgeStatus.includes('suspenso')) mostrar = false;
        if (status === 'revisao' && !badgeStatus.includes('revisão')) mostrar = false;
      }

      // Filtro de frequência
      if (frequencia && !periodicidade.includes(frequencia)) mostrar = false;

      // Filtro de responsável (Mock: como não há na tabela, se não encontrar no texto ignora ou apenas esconde)
      if (responsavel) {
          // Ocultaremos caso o nome não exista em lugar nenhum da linha.
          const textoLinha = linha.textContent.toLowerCase();
          if (!textoLinha.includes(responsavel)) {
              // Para fins de demonstração visual sem dados reais, não vamos ocultar tudo, 
              // apenas se quisermos ser estritos. Vamos deixar a cargo da simulação.
          }
      }

      linha.style.display = mostrar ? '' : 'none';
      linha.style.transition = 'opacity 0.3s ease';
      linha.style.opacity = mostrar ? '1' : '0';
    });
  }

  function inicializarFiltros() {
    const formFiltros = document.getElementById('formFiltrosPlanos');
    if (!formFiltros) return;

    formFiltros.addEventListener('submit', (e) => {
      e.preventDefault();
      aplicarFiltros();
    });

    document.getElementById('btnLimparFiltros')?.addEventListener('click', () => {
      formFiltros.reset();
      aplicarFiltros();
    });

    // Busca em tempo real
    document.getElementById('filtroBuscaAluno')?.addEventListener('input', aplicarFiltros);
    document.getElementById('filtroStatus')?.addEventListener('change', aplicarFiltros);
    document.getElementById('filtroResponsavel')?.addEventListener('change', aplicarFiltros);
    document.getElementById('filtroFrequencia')?.addEventListener('change', aplicarFiltros);
  }

  // -------------------------------------------------------------------------
  // Inicialização Geral
  // -------------------------------------------------------------------------
  function init() {
    preencherPerfil();
    inicializarSair();
    setarDatasPadrao();
    carregarAlunos();
    carregarMétricas();
    carregarTabelaPlanos(1);
    inicializarFormulario();
    inicializarFiltros();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
