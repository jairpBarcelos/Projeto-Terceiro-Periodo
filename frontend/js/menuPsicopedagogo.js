/**
 * menuPsicopedagogo.js
 * Controlador do menu inicial/dashboard do Psicopedagogo.
 */

(function () {
  'use strict';

  // -------------------------------------------------------------------------
  // Elementos DOM
  // -------------------------------------------------------------------------
  const nomeUsuarioEl = document.getElementById('nomeUsuario');
  const nomeInstituicaoEl = document.getElementById('nomeInstituicao');
  const btnSair = document.getElementById('btnSair');

  const totalCasosEl = document.getElementById('totalCasos');
  const totalTriagensEl = document.getElementById('totalTriagens');
  const totalPlanosEl = document.getElementById('totalPlanos');
  const totalAtendimentosEl = document.getElementById('totalAtendimentos');
  const totalEncaminhamentosEl = document.getElementById('totalEncaminhamentos');

  // -------------------------------------------------------------------------
  // Perfil e Autenticação
  // -------------------------------------------------------------------------
  function preencherPerfil() {
    try {
      const user = JSON.parse(localStorage.getItem('saadi_user_info') || '{}');
      if (user && user.nome) {
        if (nomeUsuarioEl) {
          nomeUsuarioEl.textContent = `Bem-vindo(a), ${user.nome.split(' ')[0]}!`;
        }
        if (nomeInstituicaoEl && user.unidade_nome) {
          nomeInstituicaoEl.textContent = user.unidade_nome;
        } else if (nomeInstituicaoEl) {
          nomeInstituicaoEl.textContent = 'Unidade Escolar Geral';
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
  // Métricas do Dashboard
  // -------------------------------------------------------------------------
  async function carregarDashboard() {
    try {
      const resp = await fetch('/api/psicopedagogo/dashboard', {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });

      if (!resp.ok) {
        console.warn('[SAADI] Dashboard psicopedagógico indisponível:', resp.status);
        return;
      }

      const json = await resp.json();
      const d = json.data ?? json;

      // Atualiza os contadores no DOM com fallback seguro
      if (totalCasosEl) totalCasosEl.textContent = d.casos_ativos ?? '0';
      if (totalTriagensEl) totalTriagensEl.textContent = d.triagens_pendentes ?? '0';
      if (totalPlanosEl) totalPlanosEl.textContent = d.planos_ativos ?? '0';
      if (totalAtendimentosEl) totalAtendimentosEl.textContent = d.atendimentos_hoje ?? '0';
      if (totalEncaminhamentosEl) totalEncaminhamentosEl.textContent = d.encaminhamentos_abertos ?? '0';

    } catch (err) {
      console.error('[SAADI] Erro ao carregar métricas do dashboard:', err);
    }
  }

  // -------------------------------------------------------------------------
  // Inicialização
  // -------------------------------------------------------------------------
  function init() {
    preencherPerfil();
    inicializarSair();
    carregarDashboard();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
