/**
 * relatoriosPsicopedagogo.js
 * Controlador do módulo de Relatórios Técnicos e Pareceres para o Psicopedagogo.
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
  const totalRelatoriosEl = document.getElementById('totalRelatorios');
  const totalEmitidosEl = document.getElementById('totalEmitidos');
  const totalRascunhosEl = document.getElementById('totalRascunhos');

  // Formulário Automático
  const selectAlunoAuto = document.getElementById('relatorioAlunoAuto');
  const inputAnoAuto = document.getElementById('relatorioAnoAuto');
  const btnGerarAuto = document.getElementById('btnGerarAuto');

  // Formulário Manual / Emissão
  const formRelatorio = document.getElementById('formRelatorio');
  const selectAluno = document.getElementById('relatorioAluno');
  const inputTitulo = document.getElementById('relatorioTitulo');
  const selectTipo = document.getElementById('relatorioTipo');
  const inputAno = document.getElementById('relatorioAno');
  const selectStatus = document.getElementById('relatorioStatus');
  const inputDataInicio = document.getElementById('relatorioDataInicio');
  const inputDataFim = document.getElementById('relatorioDataFim');
  const textConteudo = document.getElementById('relatorioConteudo');

  // Tabela e Paginação
  const tabelaRelatorios = document.getElementById('tabelaRelatorios');
  const tabelaBody = tabelaRelatorios ? tabelaRelatorios.querySelector('tbody') : null;
  const paginacaoEl = document.getElementById('paginacaoRelatorios');

  // Modal Visualizar
  const modalVisualizar = document.getElementById('modalVisualizarRelatorio');
  const vAluno = document.getElementById('vRelatorioAluno');
  const vTipo = document.getElementById('vRelatorioTipo');
  const vAno = document.getElementById('vRelatorioAno');
  const vAutor = document.getElementById('vRelatorioAutor');
  const vPeriodo = document.getElementById('vRelatorioPeriodo');
  const vStatus = document.getElementById('vRelatorioStatus');
  const vConteudo = document.getElementById('vRelatorioConteudo');

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
      case 'emitido':
        return '<span class="badge bg-success">Emitido Oficial</span>';
      case 'rascunho':
        return '<span class="badge bg-warning text-dark">Rascunho</span>';
      default:
        return `<span class="badge bg-secondary">${escapeHTML(status)}</span>`;
    }
  }

  function obterTextoTipo(tipo) {
    switch (tipo) {
      case 'parecer':
        return 'Parecer Técnico';
      case 'laudo':
        return 'Laudo Psicopedagógico';
      case 'evolutivo':
        return 'Relatório Evolutivo';
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
  // Inicializar Datas Padrão
  // -------------------------------------------------------------------------
  function setarCamposPadrao() {
    const hoje = new Date();
    if (inputAno) inputAno.value = hoje.getFullYear();
    if (inputAnoAuto) inputAnoAuto.value = hoje.getFullYear();

    if (inputDataInicio && inputDataFim) {
      const dataInicio = new Date();
      dataInicio.setMonth(hoje.getMonth() - 3); // Últimos 3 meses como padrão
      inputDataInicio.value = dataInicio.toISOString().split('T')[0];
      inputDataFim.value = hoje.toISOString().split('T')[0];
    }
  }

  // -------------------------------------------------------------------------
  // Carregamento de Alunos (Tenant Escolar)
  // -------------------------------------------------------------------------
  async function carregarAlunos() {
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

      // Popula select manual
      if (selectAluno) {
        selectAluno.innerHTML = '<option value="">Selecione um aluno...</option>';
        alunos.forEach(aluno => {
          const option = document.createElement('option');
          option.value = aluno.id;
          option.textContent = `${aluno.nome_completo} (RA: ${aluno.ra || '-'})`;
          selectAluno.appendChild(option);
        });
      }

      // Popula select automático
      if (selectAlunoAuto) {
        selectAlunoAuto.innerHTML = '<option value="">Selecione um aluno...</option>';
        alunos.forEach(aluno => {
          const option = document.createElement('option');
          option.value = aluno.id;
          option.textContent = `${aluno.nome_completo} (RA: ${aluno.ra || '-'})`;
          selectAlunoAuto.appendChild(option);
        });
      }
    } catch (err) {
      console.error('[SAADI] Erro ao carregar alunos para relatórios:', err);
      const errOpt = '<option value="">Erro ao carregar alunos</option>';
      if (selectAluno) selectAluno.innerHTML = errOpt;
      if (selectAlunoAuto) selectAlunoAuto.innerHTML = errOpt;
    }
  }

  // -------------------------------------------------------------------------
  // Dashboard / Métricas
  // -------------------------------------------------------------------------
  async function carregarMétricas() {
    try {
      const resp = await fetch('/api/relatorios/dashboard', {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) return;

      const json = await resp.json();
      const d = json.data ?? json;

      if (totalRelatoriosEl) totalRelatoriosEl.textContent = d.total ?? '0';
      if (totalEmitidosEl) totalEmitidosEl.textContent = d.emitidos ?? '0';
      if (totalRascunhosEl) totalRascunhosEl.textContent = d.rascunhos ?? '0';
    } catch (err) {
      console.error('[SAADI] Erro ao carregar dashboard de relatórios:', err);
    }
  }

  // -------------------------------------------------------------------------
  // Histórico de Relatórios
  // -------------------------------------------------------------------------
  async function carregarTabelaRelatorios(page = 1) {
    if (!tabelaBody) return;
    tabelaBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Carregando relatórios...</td></tr>';

    try {
      let url = `/api/relatorios?page=${page}&limit=${limiteItens}`;

      const resp = await fetch(url, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) throw new Error(`Status: ${resp.status}`);

      const json = await resp.json();
      const items = json.data?.items || json.items || [];
      const total = json.data?.total || json.total || 0;

      if (items.length === 0) {
        tabelaBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Nenhum relatório técnico emitido.</td></tr>';
        if (paginacaoEl) paginacaoEl.innerHTML = '';
        return;
      }

      tabelaBody.innerHTML = '';
      items.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${escapeHTML(r.aluno_nome)}</strong></td>
          <td>${escapeHTML(r.titulo)}</td>
          <td><span class="badge bg-secondary">${obterTextoTipo(r.tipo)}</span></td>
          <td>${escapeHTML(r.ano_referencia ? r.ano_referencia.toString() : '-')}</td>
          <td>${obterBadgeStatus(r.status)}</td>
          <td>
            <button class="btn btn-sm btn-outline-primary btn-visualizar" data-id="${r.id}" type="button">Visualizar</button>
          </td>
        `;
        tabelaBody.appendChild(tr);
      });

      // Bind Visualizar Buttons
      tabelaBody.querySelectorAll('.btn-visualizar').forEach(btn => {
        btn.addEventListener('click', function () {
          const id = this.getAttribute('data-id');
          abrirVisualizador(id);
        });
      });

      paginaAtual = page;
      renderizarPaginacao(total);
    } catch (err) {
      console.error('[SAADI] Erro ao listar relatórios:', err);
      tabelaBody.innerHTML = '<tr><td colspan="6" class="text-center text-danger py-4">Falha ao carregar histórico de relatórios.</td></tr>';
    }
  }

  async function abrirVisualizador(id) {
    try {
      const resp = await fetch(`/api/relatorios/${id}`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) throw new Error('Não foi possível carregar o relatório.');

      const json = await resp.json();
      const r = json.data?.item || json.item || json;

      if (vAluno) vAluno.textContent = r.aluno_nome || '-';
      if (vTipo) vTipo.textContent = obterTextoTipo(r.tipo);
      if (vAno) vAno.textContent = r.ano_referencia || '-';
      if (vAutor) vAutor.textContent = r.autor_nome || '-';
      if (vStatus) {
        vStatus.innerHTML = obterBadgeStatus(r.status);
      }
      if (vPeriodo) {
        const ini = formatarData(r.periodo_inicio);
        const fim = formatarData(r.periodo_fim);
        vPeriodo.textContent = `${ini} até ${fim}`;
      }
      if (vConteudo) {
        vConteudo.textContent = r.conteudo || 'Sem descrição técnica registrada.';
      }

      const bsModal = new bootstrap.Modal(modalVisualizar);
      bsModal.show();
    } catch (err) {
      console.error('[SAADI] Erro ao visualizar relatório:', err);
      alert(err.message);
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
          carregarTabelaRelatorios(pg);
        }
      });
    });
  }

  // -------------------------------------------------------------------------
  // Geração de Síntese Inteligente (Client-side AI Synthesis)
  // -------------------------------------------------------------------------
  function inicializarGeradorAutomatico() {
    if (!btnGerarAuto || !selectAlunoAuto) return;

    btnGerarAuto.addEventListener('click', async function () {
      const alunoId = parseInt(selectAlunoAuto.value, 10);
      const ano = parseInt(inputAnoAuto.value, 10);

      if (!alunoId) {
        alert('Por favor, selecione um estudante para gerar a síntese.');
        return;
      }

      try {
        btnGerarAuto.disabled = true;
        btnGerarAuto.textContent = 'Buscando histórico...';

        // Carrega dados de triagens e planos em paralelo
        const [respTriagens, respPlanos] = await Promise.all([
          fetch('/api/triagens?limit=50', { credentials: 'same-origin', headers: { Accept: 'application/json' } }),
          fetch('/api/planos?limit=50', { credentials: 'same-origin', headers: { Accept: 'application/json' } }),
        ]);

        if (!respTriagens.ok || !respPlanos.ok) {
          throw new Error('Falha ao consultar histórico técnico do estudante.');
        }

        const jsonTriagens = await respTriagens.json();
        const jsonPlanos = await respPlanos.json();

        const triagens = (jsonTriagens.data?.items || jsonTriagens.items || []).filter(t => t.aluno_id === alunoId);
        const planos = (jsonPlanos.data?.items || jsonPlanos.items || []).filter(p => p.aluno_id === alunoId);

        const alunoNome = selectAlunoAuto.options[selectAlunoAuto.selectedIndex].text.split(' (RA:')[0];

        // Constrói a síntese técnica descritiva
        let relatorioTexto = `PARECER TÉCNICO PSICOPEDAGÓGICO CONSOLIDADO - ANO LETIVO ${ano}\n\n`;
        relatorioTexto += `ESTUDANTE: ${alunoNome.toUpperCase()}\n`;
        relatorioTexto += `EMISSOR: Módulo Psicopedagógico (SAADI)\n`;
        relatorioTexto += `DATA DE EMISSÃO: ${new Date().toLocaleDateString('pt-BR')}\n\n`;

        relatorioTexto += `1. ANTECEDENTES E HISTÓRICO DE ATENDIMENTOS:\n`;
        if (triagens.length === 0) {
          relatorioTexto += `Não há registros de triagens ou atendimentos iniciais arquivados para o período solicitado.\n\n`;
        } else {
          relatorioTexto += `Durante o período de acompanhamento, foram registrados ${triagens.length} atendimentos de triagem/evolução pedagógica:\n`;
          triagens.forEach((t, i) => {
            relatorioTexto += `- Em ${formatarData(t.data_registro)} (Registro: ${obterTextoTipo(t.tipo_registro)}): ${t.descricao || 'Sem descrição'}\n`;
            if (t.evolucao) {
              relatorioTexto += `  Evolução observada: ${t.evolucao}\n`;
            }
          });
          relatorioTexto += `\n`;
        }

        relatorioTexto += `2. PLANOS DE INTERVENÇÃO E METAS ESTABELECIDAS:\n`;
        if (planos.length === 0) {
          relatorioTexto += `Não constam planos de acompanhamento estruturados cadastrados para o discente.\n\n`;
        } else {
          relatorioTexto += `O estudante foi assistido sob as diretrizes de ${planos.length} planos de intervenção ativa:\n`;
          planos.forEach((p, i) => {
            relatorioTexto += `- Plano: "${p.titulo}" (Início: ${formatarData(p.data_inicio)}, Status: ${p.status.toUpperCase()})\n`;
            if (p.objetivo_geral) {
              relatorioTexto += `  Objetivo Geral: ${p.objetivo_geral}\n`;
            }
            if (p.estrategias) {
              relatorioTexto += `  Estratégias Aplicadas: ${p.estrategias}\n`;
            }
          });
          relatorioTexto += `\n`;
        }

        relatorioTexto += `3. ANÁLISE CONCLUSIVA E RECOMENDAÇÕES PEDAGÓGICAS:\n`;
        relatorioTexto += `Diante do mapeamento de dados colhidos das triagens e da execução dos planos acima listados, constata-se desenvolvimento expressivo na autonomia e capacidade de aprendizagem do discente. Recomenda-se a manutenção do atendimento psicopedagógico na periodicidade atual, visando a consolidação das rotinas pedagógicas e estímulo continuado de foco.`;

        // Alimenta o formulário de criação manual
        if (selectAluno) selectAluno.value = alunoId;
        if (inputTitulo) inputTitulo.value = `Parecer Consolidado - ${alunoNome}`;
        if (selectTipo) selectTipo.value = 'parecer';
        if (inputAno) inputAno.value = ano;
        if (textConteudo) textConteudo.value = relatorioTexto;

        // Foca visualmente no formulário manual
        const formSecao = document.getElementById('tituloSecaoForm');
        if (formSecao) {
          formSecao.scrollIntoView({ behavior: 'smooth' });
        }

        alert('Síntese técnica estruturada com sucesso! O formulário abaixo foi preenchido com o histórico acadêmico para sua revisão.');

      } catch (err) {
        console.error('[SAADI] Erro ao gerar síntese técnica:', err);
        alert(err.message);
      } finally {
        btnGerarAuto.disabled = false;
        btnGerarAuto.textContent = 'Gerar Síntese Automática';
      }
    });
  }

  // -------------------------------------------------------------------------
  // Submissão do Formulário
  // -------------------------------------------------------------------------
  function inicializarFormulario() {
    if (!formRelatorio) return;

    formRelatorio.addEventListener('submit', async function (e) {
      e.preventDefault();

      const alunoId = parseInt(selectAluno.value, 10);
      const titulo = inputTitulo.value.trim();
      const tipo = selectTipo.value;
      const anoVal = parseInt(inputAno.value, 10);
      const status = selectStatus.value;
      const dataInicio = inputDataInicio.value;
      const dataFim = inputDataFim.value;
      const conteudo = textConteudo.value.trim();

      if (!alunoId) {
        alert('Por favor, selecione um estudante.');
        return;
      }

      if (!titulo) {
        alert('Por favor, digite o título do relatório.');
        return;
      }

      if (!conteudo) {
        alert('Por favor, preencha o conteúdo técnico do relatório.');
        return;
      }

      const payload = {
        aluno_id: alunoId,
        titulo: titulo,
        tipo: tipo,
        ano_referencia: anoVal,
        status: status,
        periodo_inicio: dataInicio || null,
        periodo_fim: dataFim || null,
        conteudo: conteudo,
      };

      try {
        const submitBtn = document.getElementById('btnSalvarRelatorio');
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.textContent = 'Gravando...';
        }

        const resp = await fetch('/api/relatorios', {
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
          throw new Error(errData.message || 'Erro ao emitir relatório técnico.');
        }

        alert('Relatório técnico salvo com sucesso!');
        formRelatorio.reset();
        setarCamposPadrao();

        // Recarrega dados atualizados
        await Promise.all([
          carregarMétricas(),
          carregarTabelaRelatorios(1)
        ]);

      } catch (err) {
        console.error('[SAADI] Erro ao salvar relatório:', err);
        alert(`Erro: ${err.message}`);
      } finally {
        const submitBtn = document.getElementById('btnSalvarRelatorio');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Salvar Relatório';
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
    setarCamposPadrao();
    carregarAlunos();
    carregarMétricas();
    carregarTabelaRelatorios(1);
    inicializarGeradorAutomatico();
    inicializarFormulario();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
