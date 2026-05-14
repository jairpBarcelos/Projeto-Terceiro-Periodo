/**
 * secretariaCommon.js – Módulo compartilhado para TODAS as páginas da Secretaria Escolar.
 * 
 * Responsabilidades:
 *  - Verificar autenticação (redireciona para login se 401)
 *  - Carregar e exibir perfil do usuário logado na sidebar
 *  - Logout real via API (revoga JWT)
 *  - Helper para chamadas autenticadas
 */

;(function () {
    'use strict';

    const API_BASE = '/api';

    // ─── HELPERS ───────────────────────────────────────────────
    async function fetchAutenticado(url, opcoes = {}) {
        const defaults = {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json', ...(opcoes.headers || {}) },
        };
        const response = await fetch(url, { ...defaults, ...opcoes });
        if (response.status === 401) {
            window.location.href = '/index.html';
            throw new Error('Não autenticado');
        }
        return response;
    }

    async function lerJsonSeguro(response) {
        try { return await response.json(); } catch { return {}; }
    }

    // ─── PERFIL DO USUÁRIO ────────────────────────────────────
    async function carregarPerfilLogado() {
        try {
            const response = await fetchAutenticado(`${API_BASE}/auth/me`);
            const dados = await lerJsonSeguro(response);
            const fonte = dados.data || dados;

            // Atualizar nome na sidebar
            const nomeEl = document.querySelector('.Perfil p');
            if (nomeEl) {
                const nome = fonte.user_name || fonte.nome_completo || '';
                const primeiro = nome.split(' ')[0];
                nomeEl.textContent = primeiro ? `Bem-vindo(a), ${primeiro}!` : 'Bem-vindo(a)!';
            }

            // Atualizar nome da instituição, se existir o elemento
            const instEl = document.getElementById('nomeInstituicao');
            if (instEl) {
                instEl.textContent = fonte.unidade_nome || fonte.unit_name || 'Instituição não vinculada';
            }

            // Guardar dados do perfil para uso em outros scripts
            window.__saadiPerfil = {
                id: fonte.user_id || fonte.id,
                nome: fonte.user_name || fonte.nome_completo,
                email: fonte.email,
                cpf: fonte.cpf,
                perfil: fonte.profile_name || fonte.perfil_nome,
                unidade_id: fonte.unit_id || fonte.unidade_id,
                unidade_nome: fonte.unidade_nome || fonte.unit_name,
            };

            preencherModalPerfil(window.__saadiPerfil);

            return window.__saadiPerfil;
        } catch (e) {
            console.error('Erro ao carregar perfil:', e);
            return null;
        }
    }

    // ─── LOGOUT ───────────────────────────────────────────────
    function logout() {
        if (!confirm('Tem certeza que deseja sair do sistema?')) return;
        fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' },
        }).finally(() => {
            localStorage.removeItem('saadi_user_info');
            window.location.href = '/index.html';
        });
    }

    // ─── MODAL PERFIL ────────────────────────────────────────
    function preencherModalPerfil(perfil) {
        const modal = document.getElementById('modalConfiguracoesUsuario');
        if (!modal) return;

        const nomeInput = modal.querySelector('#nomeExibicao');
        const emailInput = modal.querySelector('#emailInstitucional');
        const cpfInput = modal.querySelector('#cpfUsuario');

        if (nomeInput) nomeInput.value = perfil.nome || '';
        if (emailInput) emailInput.value = perfil.email || '';
        if (cpfInput) cpfInput.value = perfil.cpf || '';

        const form = modal.querySelector('#formConfiguracoesUsuario');
        if (form && !form.dataset.ready) {
            form.dataset.ready = 'true';
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const btn = form.querySelector('button[type="submit"]');
                const originalText = btn.textContent;
                btn.textContent = 'Salvando...';
                btn.disabled = true;

                const payload = {
                    nome_completo: form.querySelector('#nomeExibicao').value.trim(),
                };

                const novaSenha = form.querySelector('#novaSenha')?.value;
                if (novaSenha) payload.senha = novaSenha;

                try {
                    const resp = await fetchAutenticado(`${API_BASE}/auth/me`, {
                        method: 'PUT',
                        body: JSON.stringify(payload),
                        headers: { 'Content-Type': 'application/json' }
                    });

                    if (resp.ok) {
                        alert('Perfil atualizado com sucesso!');
                        // Recarregar perfil para atualizar sidebar
                        await carregarPerfilLogado();
                        // Fechar modal via Bootstrap
                        const bsModal = bootstrap.Modal.getInstance(modal);
                        if (bsModal) bsModal.hide();
                    } else {
                        const erro = await lerJsonSeguro(resp);
                        alert(erro.message || 'Erro ao atualizar perfil.');
                    }
                } catch (err) {
                    console.error('Erro ao salvar perfil:', err);
                    alert('Erro de conexão.');
                } finally {
                    btn.textContent = originalText;
                    btn.disabled = false;
                }
            });
        }
    }

    // ─── INICIALIZAÇÃO ────────────────────────────────────────
    function substituirLogoutLinks() {
        // Troca todos os <a href="...login.html"> por logout real
        document.querySelectorAll('a.textoSair, a[href*="login.html"]').forEach(link => {
            link.removeAttribute('href');
            link.style.cursor = 'pointer';
            link.addEventListener('click', (e) => {
                e.preventDefault();
                logout();
            });
        });
    }

    // Auto-inicializar ao carregar
    document.addEventListener('DOMContentLoaded', () => {
        substituirLogoutLinks();
        carregarPerfilLogado();
    });

    // Expor para uso em scripts inline
    window.secretariaCommon = {
        fetchAutenticado,
        lerJsonSeguro,
        carregarPerfilLogado,
        logout,
        API_BASE,
    };
})();
