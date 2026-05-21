/**
 * encaminhamentosSecretaria.js
 * 
 * Controlador frontend para a página de Encaminhamentos da Secretaria Escolar.
 * Integrado perfeitamente com as APIs centrais do SAADI.
 */

(function () {
    'use strict';

    // ─── UTILS & CAPAS ───────────────────────────────────────────
    function escapeHTML(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;')
                  .replace(/"/g, '&quot;')
                  .replace(/'/g, '&#039;');
    }

    function formatarData(isoString) {
        if (!isoString) return '';
        const d = new Date(isoString);
        if (isNaN(d.getTime())) return isoString;
        return d.toLocaleDateString('pt-BR');
    }

    const TIPO_LABEL = { interno: 'Interno', externo: 'Externo' };
    const PRIORIDADE_LABEL = { alta: 'Alta', media: 'Média', baixa: 'Baixa' };
    const STATUS_LABEL = {
        aberto: 'Aberto',
        retorno_recebido: 'Retorno Recebido',
        sem_retorno: 'Sem Retorno',
        concluido: 'Concluído',
        cancelado: 'Cancelado',
        em_andamento: 'Em andamento'
    };

    // ─── ELEMENTOS DO DOM ───────────────────────────────────────
    const selectAluno = document.getElementById('aluno');
    const selectTipo = document.getElementById('tipo');
    const selectDestino = document.getElementById('destino');
    const selectPrioridade = document.getElementById('prioridade');
    const inputPrazo = document.getElementById('prazo_retorno');
    const textareaDescricao = document.getElementById('mensagem');
    const formEncaminhamento = document.getElementById('formNovoEncaminhamento');
    const containerFila = document.getElementById('filaEncaminhamentos');
    const btnEnviar = document.getElementById('btnEnviar');

    let perfilUsuario = null;

    // ─── CARREGAR ALUNOS ────────────────────────────────────────
    async function carregarAlunos(unidadeId) {
        try {
            const url = unidadeId
                ? `/api/alunos?unidade_id=${unidadeId}&limit=100`
                : '/api/alunos?limit=100';

            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const json = await response.json();
            const alunos = json.data?.items || json.items || [];

            if (alunos.length === 0) {
                selectAluno.innerHTML = '<option value="">Nenhum aluno ativo cadastrado</option>';
                return;
            }

            selectAluno.innerHTML = '<option value="">Selecione o aluno</option>' + 
                alunos.map(aluno => `
                    <option value="${aluno.id}">${escapeHTML(aluno.nome_completo)} (${escapeHTML(aluno.serie_turma || 'Série não informada')})</option>
                `).join('');

        } catch (err) {
            console.error('[SAADI] Erro ao carregar alunos:', err);
            selectAluno.innerHTML = '<option value="">Erro ao carregar alunos. Tente recarregar.</option>';
        }
    }

    // ─── CARREGAR FILA DE ENCAMINHAMENTOS ──────────────────────
    async function carregarFila() {
        if (!containerFila) return;

        try {
            const params = new URLSearchParams({ limit: 50 });
            if (perfilUsuario && perfilUsuario.id) {
                params.append('solicitante_id', perfilUsuario.id);
            }

            const response = await fetch(`/api/encaminhamentos?${params}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const json = await response.json();
            const items = json.items || json.data?.items || [];

            if (items.length === 0) {
                containerFila.innerHTML = `
                    <div style="text-align: center; padding: 30px; color: #777; font-size: 0.9rem;">
                        Nenhum encaminhamento registrado por você.
                    </div>
                `;
                return;
            }

            containerFila.innerHTML = items.map(enc => {
                const tipoCls = enc.tipo === 'externo' ? 'style="border-color: #17a2b8; background: #eef9fa;"' : '';
                const prazoHtml = enc.prazo_retorno 
                    ? `<span>Prazo: ${escapeHTML(formatarData(enc.prazo_retorno))}</span>` 
                    : '';

                const prioridadeCls = enc.prioridade === 'alta' ? 'style="background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;"' : 
                                      enc.prioridade === 'media' ? 'style="background: #fff3cd; color: #856404; border: 1px solid #ffeeba;"' : 
                                      'style="background: #e2e3e5; color: #383d41; border: 1px solid #d6d8db;"';

                const statusCls = enc.status === 'concluido' ? 'style="background: #d4edda; color: #155724; border: 1px solid #c3e6cb;"' :
                                  enc.status === 'aberto' ? 'style="background: #fff3cd; color: #856404; border: 1px solid #ffeeba;"' :
                                  'style="background: #e2e3e5; color: #383d41; border: 1px solid #d6d8db;"';

                return `
                    <div class="cardEncaminhamento" ${tipoCls}>
                        <h3>${escapeHTML(enc.aluno_nome || 'Aluno')} &rarr; ${escapeHTML(enc.destino)}</h3>
                        <div class="metaEncaminhamento">
                            <span>${escapeHTML(TIPO_LABEL[enc.tipo] || enc.tipo)}</span>
                            <span ${prioridadeCls}>${escapeHTML(PRIORIDADE_LABEL[enc.prioridade] || enc.prioridade)}</span>
                            ${prazoHtml}
                            <span ${statusCls}>Status: ${escapeHTML(STATUS_LABEL[enc.status] || enc.status)}</span>
                        </div>
                        <p>${escapeHTML(enc.descricao)}</p>
                    </div>
                `;
            }).join('');

        } catch (err) {
            console.error('[SAADI] Erro ao carregar fila:', err);
            containerFila.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #d9534f; font-size: 0.9rem;">
                    Erro ao conectar com a fila de encaminhamentos.
                </div>
            `;
        }
    }

    // ─── SUBMETER ENCAMINHAMENTO ────────────────────────────────
    async function enviarEncaminhamento(e) {
        e.preventDefault();

        const alunoId = parseInt(selectAluno.value, 10);
        const tipo = selectTipo.value;
        const destino = selectDestino.value;
        const prioridade = selectPrioridade.value;
        const descricao = textareaDescricao.value.trim();
        const prazo_retorno = inputPrazo.value || null;

        if (!alunoId || !tipo || !destino || !prioridade || !descricao) {
            alert('Por favor, preencha todos os campos obrigatórios.');
            return;
        }

        if (descricao.length < 5) {
            alert('A descrição da demanda precisa ter no mínimo 5 caracteres.');
            return;
        }

        const payload = {
            aluno_id: alunoId,
            tipo: tipo,
            destino: destino,
            prioridade: prioridade,
            descricao: descricao,
            prazo_retorno: prazo_retorno
        };

        const originalBtnText = btnEnviar.textContent;
        btnEnviar.textContent = 'Enviando...';
        btnEnviar.disabled = true;

        try {
            const response = await fetch('/api/encaminhamentos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                alert('Encaminhamento realizado com sucesso!');
                formEncaminhamento.reset();
                carregarFila();
            } else {
                alert(data.message || 'Erro ao registrar encaminhamento no servidor.');
            }

        } catch (err) {
            console.error('[SAADI] Erro de conexão:', err);
            alert('Falha de conexão com o servidor. Verifique sua rede.');
        } finally {
            btnEnviar.textContent = originalBtnText;
            btnEnviar.disabled = false;
        }
    }

    // ─── INICIALIZAÇÃO ──────────────────────────────────────────
    async function inicializar() {
        // Obter informações do usuário logado via modulo comum da secretaria
        try {
            if (window.secretariaCommon && window.secretariaCommon.carregarPerfilLogado) {
                perfilUsuario = await window.secretariaCommon.carregarPerfilLogado();
            }
        } catch (err) {
            console.warn('[SAADI] Não foi possível ler o perfil logado diretamente, buscando fallback...', err);
        }

        const unidadeId = perfilUsuario?.unidade_id;

        // Executar carregamentos paralelos
        await Promise.all([
            carregarAlunos(unidadeId),
            carregarFila()
        ]);

        // Registrar manipulador de formulário
        if (formEncaminhamento) {
            formEncaminhamento.addEventListener('submit', enviarEncaminhamento);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        inicializar();
    }
})();
